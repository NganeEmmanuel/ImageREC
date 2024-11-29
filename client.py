import grpc
import image_processing_pb2
import image_processing_pb2_grpc


def send_image_to_master(image_path):
    # Read the image file as bytes
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()  # This reads the image as binary data
    except FileNotFoundError:
        print(f"Error: File '{image_path}' not found.")
        return

    # Create a stub for communication with the master node
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = image_processing_pb2_grpc.MasterServiceStub(channel)

        # Send the image data as part of the request
        try:
            response = stub.ProcessImage(image_processing_pb2.ImageRequest(image_data=image_data))
            print("\nDescriptions of detected objects:")
            for description in response.worker_responses:
                print(description.result)
        except grpc.RpcError as e:
            print(f"Error communicating with master: {str(e)}")


if __name__ == "__main__":
    print("Client started. Enter image file paths to process them. Type 'exit' to quit.")
    while True:
        image_path = input("\nEnter image path: ")
        if image_path.lower() == "exit":
            print("Exiting client.")
            break
        send_image_to_master(image_path)
