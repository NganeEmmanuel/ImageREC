import time

import grpc
from concurrent import futures
import image_processing_pb2
import image_processing_pb2_grpc
from PIL import Image
import io
import json


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
        # Load the image and get dimensions
        image_data = request.image_data
        image = Image.open(io.BytesIO(image_data))
        image_width, image_height = image.size

        # Worker node addresses
        worker_addresses = ["localhost:50052", "localhost:50053"]

        # Send image data to workers and collect responses
        all_detections = []
        for worker_address in worker_addresses:
            print(f"Sending image data to worker at {worker_address}...")
            detections = self.send_image_to_worker(worker_address, image_data)
            all_detections.extend(detections)

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


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    image_processing_pb2_grpc.add_MasterServiceServicer_to_server(MasterServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Master server started on port 50051")
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
