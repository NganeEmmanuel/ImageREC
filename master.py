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

import image_processing_pb2
import image_processing_pb2_grpc

# Constants
BASE_WORKER_PORT = 50052
MAX_WORKERS = 10
IMAGE_SIZE_THRESHOLD_MB = 5
WORKER_IDLE_TIMEOUT = 30

# Global registries
worker_registry = {}
request_state = {}  # To store request states
request_queue = Queue()  # Thread-safe queue for incoming requests
worker_lock = Lock()
state_lock = Lock()

# Sample model data
available_models = {
    "model_1": {"description": "Object detection model v1", "accuracy": 0.85},
    "model_2": {"description": "Object detection model v2", "accuracy": 0.90},
}


# Helper function: Generate descriptions from detections
def generate_descriptions(detections, image_width, image_height):
    descriptions = []
    for detection in detections:
        obj_class = detection["class"]
        x1, y1, x2, y2 = detection["bounding_box"]
        confidence = detection["confidence"]

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
        global request_state

        # Generate a unique request ID
        request_id = str(uuid4())

        # Store the initial state as pending
        with state_lock:
            request_state[request_id] = {"status": "pending", "result": None}

        # Add request to the queue
        request_queue.put((request_id, request.image_data))
        print(f"Request {request_id} added to queue.")

        # Respond with the request ID
        return image_processing_pb2.ImageResponse(request_id=request_id)

    def QueryResult(self, request, context):
        global request_state

        request_id = request.request_id
        with state_lock:
            if request_id not in request_state:
                return image_processing_pb2.ResultResponse(
                    status="not_found",
                    result="Request ID not found."
                )

            status = request_state[request_id]["status"]
            result = request_state[request_id]["result"]

        return image_processing_pb2.ResultResponse(
            status=status,
            result=json.dumps(result) if result else ""
        )

    def GetModels(self, request, context):
        for model_name, details in available_models.items():
            yield image_processing_pb2.ModelInfo(
                model_name=model_name,
                description=details["description"],
                accuracy=details["accuracy"]
            )

    def GetModelDetails(self, request, context):
        model_name = request.model_name
        if model_name in available_models:
            details = available_models[model_name]
            return image_processing_pb2.ModelDetail(
                model_name=model_name,
                description=details["description"],
                accuracy=details["accuracy"]
            )
        return image_processing_pb2.ModelDetail(
            model_name=model_name,
            description="Model not found.",
            accuracy=0.0
        )

    def send_image_to_worker(self, worker_address, image_data):
        with grpc.insecure_channel(worker_address) as channel:
            stub = image_processing_pb2_grpc.WorkerServiceStub(channel)
            response = stub.ProcessChunk(image_processing_pb2.ChunkRequest(chunk_data=image_data))
            return json.loads(response.result)

    def check_worker_ready(self, worker_address, timeout=10):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                with grpc.insecure_channel(worker_address) as channel:
                    stub = image_processing_pb2_grpc.WorkerServiceStub(channel)
                    stub.HealthCheck(image_processing_pb2.HealthRequest())
                    return True
            except grpc.RpcError:
                time.sleep(1)
        return False

    def scale_workers(self, image_size_mb):
        global worker_registry

        required_workers = max(2, min(MAX_WORKERS, int(image_size_mb // IMAGE_SIZE_THRESHOLD_MB + 1)))

        # Start additional workers if needed
        for port in range(BASE_WORKER_PORT, BASE_WORKER_PORT + required_workers):
            worker_address = f"localhost:{port}"
            if worker_address not in worker_registry:
                self.start_worker(port)

        # Stop extra workers if there are more than required
        if len(worker_registry) > required_workers:
            for worker_address in list(worker_registry.keys())[required_workers:]:
                self.stop_worker(worker_address)

    def start_worker(self, port):
        worker_address = f"localhost:{port}"
        print(f"Starting new worker at {worker_address}...")

        python_executable = sys.executable
        worker_script = os.path.abspath("worker.py")

        process = subprocess.Popen([python_executable, worker_script, str(port)])
        if self.check_worker_ready(worker_address):
            worker_registry[worker_address] = {
                "process": process,
                "last_active": time.time()
            }
            print(f"Worker at {worker_address} is ready.")
        else:
            print(f"Worker at {worker_address} failed to start or respond.")

    def stop_worker(self, worker_address):
        print(f"Stopping worker at {worker_address}...")
        process = worker_registry[worker_address]["process"]
        process.terminate()
        del worker_registry[worker_address]


# Threads for processing requests and monitoring workers
def process_requests():
    global request_state, worker_registry

    while True:
        request_id, image_data = request_queue.get()

        image_size_mb = len(image_data) / (1024 * 1024)
        with worker_lock:
            MasterServiceServicer().scale_workers(image_size_mb)

        all_detections = []
        worker_addresses = list(worker_registry.keys())

        for worker_address in worker_addresses:
            try:
                with grpc.insecure_channel(worker_address) as channel:
                    stub = image_processing_pb2_grpc.WorkerServiceStub(channel)
                    response = stub.ProcessChunk(image_processing_pb2.ChunkRequest(chunk_data=image_data))
                    all_detections.extend(json.loads(response.result))
            except Exception as e:
                print(f"Error with worker {worker_address}: {e}")

        image = Image.open(io.BytesIO(image_data))
        descriptions = generate_descriptions(all_detections, *image.size)

        with state_lock:
            request_state[request_id] = {"status": "completed", "result": descriptions}

        print(f"Request {request_id} processed.")


def monitor_workers():
    global worker_registry
    while True:
        time.sleep(10)
        with worker_lock:
            for worker_address, worker_info in list(worker_registry.items()):
                if worker_info["process"].poll() is not None:
                    print(f"Worker at {worker_address} has stopped unexpectedly. Restarting...")
                    port = int(worker_address.split(":")[1])
                    MasterServiceServicer().start_worker(port)
                elif time.time() - worker_info["last_active"] > WORKER_IDLE_TIMEOUT:
                    print(f"Worker at {worker_address} idle for too long. Stopping...")
                    MasterServiceServicer().stop_worker(worker_address)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    image_processing_pb2_grpc.add_MasterServiceServicer_to_server(MasterServiceServicer(), server)
    server.add_insecure_port('[::]:50051')

    Thread(target=process_requests, daemon=True).start()
    Thread(target=monitor_workers, daemon=True).start()

    print("Master server started on port 50051")
    server.start()
    try:
        while True:
            time.sleep(86400)  # Run indefinitely
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
