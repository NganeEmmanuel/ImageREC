import sys
import grpc
import json
from concurrent import futures
from PIL import Image
import io
import time
import torch  # YOLOv5 requires PyTorch

import image_processing_pb2
import image_processing_pb2_grpc


class WorkerServiceServicer(image_processing_pb2_grpc.WorkerServiceServicer):
    """
    Implements the WorkerService, handling image processing tasks
    and providing health checks.
    """

    def __init__(self, worker_id, model_path="yolov5s.pt"):
        """
        Initialize the worker with a YOLOv5 model instance.

        Args:
            worker_id: Unique identifier for the worker.
            model_path: Path to the YOLOv5 model.
        """
        self.worker_id = worker_id
        print(f"Loading YOLOv5 model for worker {worker_id}...")
        # Loading the YOLOv5 model from cache or from the provided path
        try:
            self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
            print(f"Worker {worker_id} initialized with model {model_path}.")
        except Exception as e:
            print(f"Error loading model: {e}")
            sys.exit(1)

    def ProcessChunk(self, request, context):
        """
        Processes a chunk of image data and returns the result.

        Args:
            request: ChunkRequest containing chunk data.
            context: gRPC context.

        Returns:
            ChunkResponse with the result of processing.
        """
        print("Processing chunk...")
        try:
            # Load image from the received bytes
            image_data = request.chunk_data
            image = Image.open(io.BytesIO(image_data))

            # Use YOLOv5 to process the image
            results = self.model(image)
            detections = results.pandas().xyxy[0].to_dict(orient="records")

            # Return results as JSON
            result_json = json.dumps(detections)
            return image_processing_pb2.ChunkResponse(result=result_json, worker_id=self.worker_id)

        except Exception as e:
            error_msg = f"Error processing chunk: {e}"
            context.set_details(error_msg)
            context.set_code(grpc.StatusCode.INTERNAL)
            return image_processing_pb2.ChunkResponse(result="{}", worker_id=self.worker_id)

    def HealthCheck(self, request, context):
        """
        Responds to health check requests.

        Args:
            request: HealthRequest (no fields required).
            context: gRPC context.

        Returns:
            HealthResponse indicating the worker's status.
        """
        return image_processing_pb2.HealthResponse(status="ready")


def serve(worker_port, worker_id, model_path):
    """
    Starts the gRPC server for the worker.

    Args:
        worker_port: Port on which the worker listens.
        worker_id: Unique identifier for the worker.
        model_path: Path to the YOLOv5 model.
    """
    # Set up the gRPC server with a thread pool
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))  # Increase max_workers for concurrency
    image_processing_pb2_grpc.add_WorkerServiceServicer_to_server(
        WorkerServiceServicer(worker_id, model_path), server
    )

    server_address = f"[::]:{worker_port}"
    server.add_insecure_port(server_address)
    print(f"Worker {worker_id} started at {server_address}")
    server.start()

    try:
        while True:
            time.sleep(86400)  # Keep running indefinitely
    except KeyboardInterrupt:
        print(f"Worker {worker_id} shutting down.")
        server.stop(0)


if __name__ == "__main__":
    # Parse the port, worker ID, and model path from command-line arguments
    if len(sys.argv) < 4:
        print("Usage: python worker.py <port> <worker_id> <model_path>")
        sys.exit(1)

    port = int(sys.argv[1])
    worker_id = sys.argv[2]
    model_path = sys.argv[3]
    serve(port, worker_id, model_path)
