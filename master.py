import grpc
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


# Master node communication with workers
def send_image_to_worker(worker_address, image_data):
    with grpc.insecure_channel(worker_address) as channel:
        stub = image_processing_pb2_grpc.WorkerServiceStub(channel)
        response = stub.ProcessChunk(image_processing_pb2.ChunkRequest(chunk_data=image_data))
        # Parse the JSON string from the worker's response
        return json.loads(response.result)


# Main master node function
def master_node(image_path):
    # Load the image and get dimensions
    with open(image_path, 'rb') as img_file:
        image_data = img_file.read()
    image = Image.open(io.BytesIO(image_data))
    image_width, image_height = image.size

    # Worker node addresses
    worker_addresses = ["localhost:50051", "localhost:50052"]

    # Send image data to workers and collect responses
    all_detections = []
    for worker_address in worker_addresses:
        print(f"Sending image data to worker at {worker_address}...")
        detections = send_image_to_worker(worker_address, image_data)
        all_detections.extend(detections)

    # Generate descriptions for all detections
    descriptions = generate_descriptions(all_detections, image_width, image_height)

    # Print descriptions
    print("\nDescriptions of detected objects:")
    for desc in descriptions:
        print(desc)


if __name__ == "__main__":
    image_path = input("Enter image path: ")
    master_node(image_path)
