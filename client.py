import grpc
import image_processing_pb2
import image_processing_pb2_grpc


def send_image_to_master(image_path):
    """
    Sends an image to the master node for processing and prints the descriptions
    of detected objects.

    Args:
        image_path (str): Path to the image file to be sent.
    """
    # Read the image file as bytes
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()  # Read the entire image file as binary data
    except FileNotFoundError:
        print(f"Error: File '{image_path}' not found.")
        return

    # Establish a gRPC channel with the master server
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = image_processing_pb2_grpc.MasterServiceStub(channel)  # Create a stub to interact with the master server

        # Send the image data to the master server
        try:
            response = stub.ProcessImage(image_processing_pb2.ImageRequest(image_data=image_data))

            # Print the responses from the workers
            print("\nDescriptions of detected objects:")
            for description in response.worker_responses:
                print(description.result)
        except grpc.RpcError as e:
            # Handle gRPC communication errors
            print(f"Error communicating with master: {str(e)}")


if __name__ == "__main__":
    """
    Client script entry point.
    Continuously prompts the user for image paths to process. 
    Type 'exit' to exit
    """
    print("Client started. Enter image file paths to process them. Type 'exit' to quit.")
    while True:
        # Prompt user to input the path to an image
        image_path = input("\nEnter image path: ")
        if image_path.lower() == "exit":
            print("Exiting client.")
            break
        send_image_to_master(image_path)
