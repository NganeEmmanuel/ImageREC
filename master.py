import sys
import os
import time
import grpc
import json
import subprocess
from concurrent import futures
from threading import Thread, Lock
from queue import Queue
from uuid import uuid4
from PIL import Image
import io
import warnings

import auth
import database_handler
import image_processing_pb2
import image_processing_pb2_grpc

# Constants
BASE_WORKER_PORT = 50052
MAX_WORKERS = 10
MIN_WORKERS = 2
WORKER_IDLE_TIMEOUT = 30

# Global registries
worker_registry = {}
available_workers = Queue()
request_state = {}
request_queue = Queue()
worker_lock = Lock()
state_lock = Lock()

available_models = {
    "model_1": {"description": "Object detection model v1", "accuracy": 0.85},
    "model_2": {"description": "Object detection model v2", "accuracy": 0.90},
}

warnings.filterwarnings("ignore", category=FutureWarning)

def check_worker_ready(worker_address, timeout=10):
    """
    Waits for a worker to signal readiness by sending a HealthCheck.
    """
    print(f"Checking readiness of worker at {worker_address}")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with grpc.insecure_channel(worker_address) as channel:
                stub = image_processing_pb2_grpc.WorkerServiceStub(channel)
                stub.HealthCheck(image_processing_pb2.HealthRequest())
                print(f"Worker {worker_address} is ready.")
                return True
        except grpc.RpcError:
            time.sleep(1)
    print(f"Worker {worker_address} failed to respond.")
    return False


def start_worker(port):
    """
    Start a worker process at the specified port.
    """
    worker_id = f"worker_{port}"
    model_path = os.path.abspath("yolov5s.pt")  # Adjust this path based on your model files
    worker_address = f"localhost:{port}"
    print(f"Starting new worker at {worker_address}...")

    python_executable = sys.executable
    worker_script = os.path.abspath("worker.py")

    process = subprocess.Popen([python_executable, worker_script, str(port), worker_id, model_path])

    # Wait a short time to allow the worker to initialize and respond to health checks
    time.sleep(2)

    if check_worker_ready(worker_address):
        with worker_lock:
            worker_registry[worker_address] = {
                "process": process,
                "last_active": time.time()
            }
            available_workers.put(worker_address)
        print(f"Worker at {worker_address} is ready.")
    else:
        print(f"Failed to start worker at {worker_address}.")


def stop_worker(worker_address):
    """
    Stop the worker process and remove it from the registry.
    """
    print(f"Stopping worker at {worker_address}...")
    with worker_lock:
        process = worker_registry[worker_address]["process"]
        process.terminate()
        del worker_registry[worker_address]


def scale_workers(required_workers):
    """
    Adjust the number of active workers to match the required count.
    """
    global worker_registry
    current_workers = len(worker_registry)

    print(f"Scaling workers. Current: {current_workers}, Required: {required_workers}")

    # Start new workers if needed
    if current_workers < required_workers:
        print(f"Starting new workers to reach {required_workers} workers.")
        for port in range(BASE_WORKER_PORT + current_workers, BASE_WORKER_PORT + required_workers):
            start_worker(port)

    # Stop excess workers
    if current_workers > required_workers:
        excess_workers = list(worker_registry.keys())[required_workers:]
        for worker_address in excess_workers:
            stop_worker(worker_address)


def generate_descriptions(detections, image_width, image_height):
    """
    Generate human-readable descriptions based on object detection results.
    """
    descriptions = []
    for detection in detections:
        # Extract bounding box coordinates directly from 'xmin', 'ymin', 'xmax', 'ymax'
        if not all(k in detection for k in ['xmin', 'ymin', 'xmax', 'ymax']):
            print(f"Warning: Missing bounding box coordinates in detection {detection}")
            continue  # Skip this detection if any bounding box coordinates are missing

        obj_class = detection.get("name", "Unknown")  # Use 'name' as the object class
        x1, y1, x2, y2 = detection["xmin"], detection["ymin"], detection["xmax"], detection["ymax"]
        confidence = detection.get("confidence", 0.0)

        x_center = (x1 + x2) / 2
        y_center = (y1 + y2) / 2
        position = ""

        if y_center < image_height / 3:
            position += "top "
        elif y_center > 2 * image_height / 3:
            position += "bottom "
        else:
            position += "middle "

        if x_center < image_width / 3:
            position += "left"
        elif x_center > image_width / 3:
            position += "right"
        else:
            position += "center"

        description = f"{obj_class} detected at the {position} of the image with {confidence:.2f} confidence."
        descriptions.append(description)

    return descriptions


class MasterServiceServicer(image_processing_pb2_grpc.MasterServiceServicer):
    def ProcessImage(self, request, context):
        request_id = str(uuid4())
        with state_lock:
            request_state[request_id] = {"status": "pending", "result": None}
        request_queue.put((request_id, request.image_data, request.user))
        database_handler.add_request(request_id, request.user.email)
        print(f"Request {request_id} added to the queue.")
        return image_processing_pb2.ImageResponse(request_id=request_id)

    def QueryResult(self, request, context):
        request_id = request.request_id
        with state_lock:
            if request_id not in request_state:
                return image_processing_pb2.ResultResponse(status="not_found", result="Request ID not found.")
            state = request_state[request_id]
        return image_processing_pb2.ResultResponse(
            status=state["status"], result=json.dumps(state["result"]) if state["result"] else ""
        )

    def HealthCheck(self, request, context):
        return image_processing_pb2.HealthResponse(status="healthy")


# Threads
def process_requests():

    while True:
        # Wait for a request from the queue
        request_id, image_data, user_credentials = request_queue.get()

        # Before processing a request
        if not auth.authenticate_user(
                user_credentials.username, user_credentials.email, user_credentials.password
        ):
            print("Authentication failed. Request denied.")
            return

        print(f"Processing request {request_id}...")

        # Dynamically scale workers
        required_workers = max(MIN_WORKERS, min(MAX_WORKERS, request_queue.qsize()))
        print(f"Scaling workers. Current: {len(worker_registry)}, Required: {required_workers}")
        scale_workers(required_workers)

        all_detections = []

        # Distribute chunks to workers only once per request
        worker_count = 0
        while worker_count < len(worker_registry) and not available_workers.empty():
            worker_address = available_workers.get()
            print(f"Assigning task to worker {worker_address}...")
            try:
                with grpc.insecure_channel(worker_address) as channel:
                    stub = image_processing_pb2_grpc.WorkerServiceStub(channel)
                    response = stub.ProcessChunk(image_processing_pb2.ChunkRequest(chunk_data=image_data))
                    print(f"Worker {worker_address} processed chunk successfully.")
                    # Inside the process_requests function, after receiving the response:
                    # print(f"Worker {worker_address} returned detections: {response.result}")

                    all_detections.extend(json.loads(response.result))
                    database_handler.add_result(request_id, response.result, user_credentials.email)
                    with worker_lock:
                        worker_registry[worker_address]["last_active"] = time.time()
                    available_workers.put(worker_address)
                worker_count += 1
            except Exception as e:
                print(f"Worker {worker_address} failed: {e}")

        # Generate descriptions after processing is complete
        image = Image.open(io.BytesIO(image_data))
        descriptions = generate_descriptions(all_detections, *image.size)

        with state_lock:
            request_state[request_id] = {"status": "completed", "result": descriptions}

        print(f"Request {request_id} processed with {len(all_detections)} detections.")

        # Remove the request from the queue (request processing is done)
        request_queue.task_done()


def monitor_workers():
    while True:
        time.sleep(10)
        with worker_lock:
            for worker_address, info in list(worker_registry.items()):
                if info["process"].poll() is not None:
                    print(f"Worker {worker_address} stopped unexpectedly.")
                    port = int(worker_address.split(":")[1])
                    start_worker(port)
                elif time.time() - info["last_active"] > WORKER_IDLE_TIMEOUT:
                    print(f"Worker {worker_address} idle for too long. Stopping.")
                    stop_worker(worker_address)


def serve():
    # Call this at the start of the application
    # auth.initialize_config()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    image_processing_pb2_grpc.add_MasterServiceServicer_to_server(MasterServiceServicer(), server)
    server.add_insecure_port('[::]:50051')

    Thread(target=process_requests, daemon=True).start()
    Thread(target=monitor_workers, daemon=True).start()

    print("Master server started on port 50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()