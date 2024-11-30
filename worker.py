import grpc
from concurrent import futures
import time
import image_processing_pb2
import image_processing_pb2_grpc
import torch
import cv2
import numpy as np
import json  # Import for JSON serialization

# WorkerServiceServicer implements the gRPC service defined in the protobuf file
class WorkerServiceServicer(image_processing_pb2_grpc.WorkerServiceServicer):
    def __init__(self):
        """
        Initialize the worker service by loading a pre-trained YOLOv5 model for object detection.
        This model is small and efficient, suitable for handling images in real-time.
        """
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s')  # Load YOLOv5 small model

    def ProcessChunk(self, request, context):
        """
        Processes a chunk of image data sent by the master server.
        Performs object detection using YOLOv5 and returns the results.

        Args:
            request (ChunkRequest): Contains the byte-encoded image data to process.
            context (grpc.ServicerContext): Provides RPC-specific information.

        Returns:
            ChunkResponse: Contains JSON-serialized detection results and the worker's ID.
        """
        # Decode the byte data into an image
        image_data = np.frombuffer(request.chunk_data, dtype=np.uint8)
        image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

        # Perform object detection using YOLOv5
        results = self.model(image)

        # Parse the detection results
        detections = []
        for *box, conf, cls in results.xyxy[0].tolist():  # Bounding box, confidence, and class
            detections.append({
                "class": self.model.names[int(cls)],  # Convert class index to class name
                "bounding_box": [int(box[0]), int(box[1]), int(box[2]), int(box[3])],  # [x1, y1, x2, y2]
                "confidence": float(conf)  # Convert confidence to float
            })

        # Log the processed results
        print(f"Processed chunk with {len(detections)} detections: {detections}")

        # Return the results as a JSON string in the response
        return image_processing_pb2.ChunkResponse(
            result=json.dumps(detections),  # Serialize detections to a JSON string
            worker_id=f"Worker-{context.peer()}"  # Use the client information for worker identification
        )

    def HealthCheck(self, request, context):
        """
        Responds to health check requests from the master server.
        Used to confirm that the worker is operational.

        Args:
            request (HealthRequest): A simple health check request.
            context (grpc.ServicerContext): Provides RPC-specific information.

        Returns:
            HealthResponse: Indicates the worker's health status.
        """
        return image_processing_pb2.HealthResponse(status="Healthy")

def serve(port):
    """
    Starts the gRPC server for the worker service on the specified port.

    Args:
        port (str): The port on which the worker service will listen for requests.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))  # Allow up to 10 threads for handling RPCs
    image_processing_pb2_grpc.add_WorkerServiceServicer_to_server(WorkerServiceServicer(), server)
    server.add_insecure_port(f'[::]:{port}')  # Listen on all interfaces at the specified port
    print(f"Worker server started on port {port}")

    # Start the server and keep it running
    server.start()
    try:
        while True:
            time.sleep(86400)  # Keep the server running indefinitely (1 day in seconds)
    except KeyboardInterrupt:
        server.stop(0)  # Gracefully stop the server on keyboard interruption

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python worker.py <port>")  # Notify user of correct usage
        sys.exit(1)  # Exit with error code if port is not provided

    # Start the worker server with the specified port
    serve(port=sys.argv[1])
