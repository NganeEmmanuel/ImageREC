import grpc
from concurrent import futures
import time
import image_processing_pb2
import image_processing_pb2_grpc
import torch
from yolov5 import YOLOv5
import cv2
import numpy as np


class WorkerServiceServicer(image_processing_pb2_grpc.WorkerServiceServicer):
    def __init__(self):
        # Load pre-trained YOLOv5 model
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s')  # Load YOLOv5 small model

    def ProcessChunk(self, request, context):
        # Convert byte data to image
        image_data = np.frombuffer(request.chunk_data, dtype=np.uint8)
        image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

        # Perform object detection
        results = self.model(image)

        # Parse results
        detections = []
        for *box, conf, cls in results.xyxy[0].tolist():
            detections.append({
                "class": self.model.names[int(cls)],  # Class label
                "bounding_box": [int(box[0]), int(box[1]), int(box[2]), int(box[3])],  # [x1, y1, x2, y2]
                "confidence": float(conf)  # Confidence score
            })

        # Log and return response
        print(f"Processed chunk with {len(detections)} detections.")
        return image_processing_pb2.ChunkResponse(
            result=str(detections),  # Serialize detections as string
            worker_id="Worker-50051"  # Example worker ID
        )


def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    image_processing_pb2_grpc.add_WorkerServiceServicer_to_server(WorkerServiceServicer(), server)
    server.add_insecure_port(f'[::]:{port}')
    print(f"Worker server started on port {port}")
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python worker.py <port>")
        sys.exit(1)
    serve(port=sys.argv[1])
