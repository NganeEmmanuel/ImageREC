import sys
import os
import time
import grpc
import json
import subprocess
from concurrent import futures
from threading import Thread, Lock
from PIL import Image
import io

import image_processing_pb2
import image_processing_pb2_grpc

# Constants for scaling logic
BASE_WORKER_PORT = 50052
MAX_WORKERS = 10
IMAGE_SIZE_THRESHOLD_MB = 5
CONCURRENT_USER_THRESHOLD = 5
WORKER_IDLE_TIMEOUT = 30  # Seconds

# Global registry for workers
worker_registry = {}
worker_lock = Lock()


# Helper function to generate descriptions
def generate_descriptions(detections, image_width, image_height):
    descriptions = []
    for detection in detections:
        obj_class = detection["class"]
        x1, y1, x2, y2 = detection["bounding_box"]
        confidence = detection["confidence"]

        # Determine object's position in the image
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
        elif x_center > 2 * image_width / 3:
            position += "right"
        else:
            position += "center"

        # Format the description
        description = f"{obj_class} detected at the {position} of the image with {confidence:.2f} confidence."
        descriptions.append(description)

    return descriptions


# MasterService implementation
class MasterServiceServicer(image_processing_pb2_grpc.MasterServiceServicer):
    def ProcessImage(self, request, context):
        global worker_registry

        # Load the image and get dimensions
        image_data = request.image_data
        image = Image.open(io.BytesIO(image_data))
        image_width, image_height = image.size

        # Scale workers based on image size and concurrent load
        image_size_mb = len(image_data) / (1024 * 1024)
        print(f"Image size: {image_size_mb:.2f} MB")
        with worker_lock:
            self.scale_workers(image_size_mb)

        # Assign workers dynamically
        all_detections = []
        with worker_lock:
            worker_addresses = list(worker_registry.keys())

        for worker_address in worker_addresses:
            try:
                print(f"Sending image data to worker at {worker_address}...")
                detections = self.send_image_to_worker(worker_address, image_data)
                all_detections.extend(detections)
            except Exception as e:
                print(f"Error with worker {worker_address}: {e}")

        # Generate descriptions for all detections
        descriptions = generate_descriptions(all_detections, image_width, image_height)

        # Prepare the response
        response = image_processing_pb2.ImageResponse()
        for description in descriptions:
            response.worker_responses.add(result=description)
        return response

    def send_image_to_worker(self, worker_address, image_data):
        with grpc.insecure_channel(worker_address) as channel:
            stub = image_processing_pb2_grpc.WorkerServiceStub(channel)
            response = stub.ProcessChunk(image_processing_pb2.ChunkRequest(chunk_data=image_data))
            # Parse the JSON string from the worker's response
            return json.loads(response.result)

    def check_worker_ready(self, worker_address, timeout=10):
        """Check if a worker is ready by invoking a HealthCheck RPC."""
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

        # Determine required workers based on image size and thresholds
        required_workers = max(2, min(MAX_WORKERS, int(image_size_mb // IMAGE_SIZE_THRESHOLD_MB + 1)))

        # Spin up additional workers if needed
        for port in range(BASE_WORKER_PORT, BASE_WORKER_PORT + required_workers):
            worker_address = f"localhost:{port}"
            if worker_address not in worker_registry:
                self.start_worker(port)

        # Terminate extra workers if needed
        if len(worker_registry) > required_workers:
            for worker_address in list(worker_registry.keys())[required_workers:]:
                self.stop_worker(worker_address)

    def start_worker(self, port):
        worker_address = f"localhost:{port}"
        print(f"Starting new worker at {worker_address}...")

        # Use the current Python interpreter explicitly
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


# Background thread to monitor worker health
def monitor_workers():
    global worker_registry
    while True:
        time.sleep(10)
        with worker_lock:
            for worker_address, worker_info in list(worker_registry.items()):
                if worker_info["process"].poll() is not None:  # Worker has exited
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
    print("Master server started on port 50051")

    # Start background worker monitoring thread
    Thread(target=monitor_workers, daemon=True).start()

    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
