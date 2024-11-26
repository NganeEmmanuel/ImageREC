import grpc
import image_processing_pb2
import image_processing_pb2_grpc


def send_image_to_master(image_path):
    # Read the image file as bytes
    with open(image_path, 'rb') as f:
        image_data = f.read()  # This reads the image as binary data

    # Create a stub for communication with the master node
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = image_processing_pb2_grpc.MasterServiceStub(channel)

        # Send the image data as part of the request
        response = stub.ProcessImage(image_processing_pb2.ImageRequest(image_data=image_data))

        # Print the response
        print("Response from master:", response)


if __name__ == "__main__":
    image_path = "repair1.jpg"  # Update this with the actual image path
    send_image_to_master(image_path)
