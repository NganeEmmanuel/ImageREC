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

# Constants for worker scaling and monitoring logic
BASE_WORKER_PORT = 50052  # Starting port for worker nodes
MAX_WORKERS = 10  # Maximum number of worker nodes allowed
IMAGE_SIZE_THRESHOLD_MB = 5  # Image size threshold to determine the number of workers
CONCURRENT_USER_THRESHOLD = 5  # Threshold for concurrent users (currently unused)
WORKER_IDLE_TIMEOUT = 30  # Timeout in seconds to stop idle workers

# Global registry to manage worker processes and their metadata
worker_registry = {}
worker_lock = Lock()  # Lock to ensure thread-safe access to worker registry


# Helper function to generate descriptions from detections
def generate_descriptions(detections, image_width, image_height):
    """
    Generate human-readable descriptions of detected objects based on their position in the image.

    Args:
        detections (list): List of detection dictionaries containing class, bounding_box, and confidence.
        image_width (int): Width of the image.
        image_height (int): Height of the image.

    Returns:
        list: A list of formatted descriptions.
    """
    descriptions = []
    for detection in detections:
        obj_class = detection["class"]
        x1, y1, x2, y2 = detection["bounding_box"]
        confidence = detection["confidence"]

        # Calculate the object's position within the image
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


# Implementation of the MasterService
class MasterServiceServicer(image_processing_pb2_grpc.MasterServiceServicer):
    """
    Implements the MasterService, which is responsible for managing image processing requests
    and coordinating worker nodes.
    """

    def ProcessImage(self, request, context):
        """
        Handles incoming image processing requests by scaling workers dynamically and dispatching tasks.

        Args:
            request: gRPC request containing image data.
            context: gRPC context object.

        Returns:
            ImageResponse: gRPC response containing results from workers.
        """
        global worker_registry

        # Load the image from the request and retrieve its dimensions
        image_data = request.image_data
        image = Image.open(io.BytesIO(image_data))
        image_width, image_height = image.size

        # Calculate image size in MB
        image_size_mb = len(image_data) / (1024 * 1024)
        print(f"Image size: {image_size_mb:.2f} MB")

        # Scale workers based on the image size
        with worker_lock:
            self.scale_workers(image_size_mb)

        # Collect results from all available workers
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

        # Generate descriptions for the detected objects
        descriptions = generate_descriptions(all_detections, image_width, image_height)

        # Prepare the gRPC response
        response = image_processing_pb2.ImageResponse()
        for description in descriptions:
            response.worker_responses.add(result=description)
        return response

    def send_image_to_worker(self, worker_address, image_data):
        """
        Sends image data to a worker node for processing.

        Args:
            worker_address (str): Address of the worker node.
            image_data (bytes): The image data to process.

        Returns:
            list: List of detections from the worker.
        """
        with grpc.insecure_channel(worker_address) as channel:
            stub = image_processing_pb2_grpc.WorkerServiceStub(channel)
            response = stub.ProcessChunk(image_processing_pb2.ChunkRequest(chunk_data=image_data))
            return json.loads(response.result)

    def check_worker_ready(self, worker_address, timeout=10):
        """
        Checks if a worker is ready by invoking a HealthCheck RPC.

        Args:
            worker_address (str): Address of the worker node.
            timeout (int): Maximum time to wait for the worker to be ready.

        Returns:
            bool: True if the worker is ready, False otherwise.
        """
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
        """
        Dynamically scales workers based on the size of the image.

        Args:
            image_size_mb (float): Size of the image in megabytes.
        """
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
        """
        Starts a new worker process on the specified port.

        Args:
            port (int): Port for the worker node.
        """
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
        """
        Stops a worker process and removes it from the registry.

        Args:
            worker_address (str): Address of the worker node.
        """
        print(f"Stopping worker at {worker_address}...")
        process = worker_registry[worker_address]["process"]
        process.terminate()
        del worker_registry[worker_address]


# Background thread to monitor and manage worker health
def monitor_workers():
    """
    Monitors worker nodes and restarts or stops them as needed.
    """
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
    """
    Starts the gRPC master server.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    image_processing_pb2_grpc.add_MasterServiceServicer_to_server(MasterServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Master server started on port 50051")

    # Start the worker monitoring thread
    Thread(target=monitor_workers, daemon=True).start()

    server.start()
    try:
        while True:
            time.sleep(86400)  # Run indefinitely
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
