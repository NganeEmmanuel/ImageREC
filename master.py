import grpc
import image_processing_pb2
import image_processing_pb2_grpc
from PIL import Image
import io


# Master node communication with workers
def send_image_to_worker(worker_address, image_data):
    with grpc.insecure_channel(worker_address) as channel:
        stub = image_processing_pb2_grpc.WorkerServiceStub(channel)
        # Send image_data wrapped in a ChunkRequest if the worker expects chunk_data
        response = stub.ProcessChunk(image_processing_pb2.ChunkRequest(chunk_data=image_data))
        return response.result  # Assuming worker returns processed data in 'result'



# Main master node function
def master_node(image_data):
    worker_addresses = ["localhost:50051", "localhost:50052"]  # Example worker nodes
    results = []

    for worker_address in worker_addresses:
        print(f"Sending image data to worker at {worker_address}...")
        processed_data = send_image_to_worker(worker_address, image_data)
        results.append(processed_data)

    print(f"Master node received processed data from workers: {results}")
    return results


if __name__ == "__main__":
    # You can pass image data from the client dynamically
    image_path = input("Enter image path: ")
    with open(image_path, 'rb') as img_file:
        image_data = img_file.read()

    # Call master node function with the image data
    master_node(image_data)
