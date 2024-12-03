import argparse
import grpc
import image_processing_pb2
import image_processing_pb2_grpc
import sys


def detect_image(image_path):
    """
    Sends an image to the master for processing and returns a request ID.
    """
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
    except FileNotFoundError:
        print(f"Error: File '{image_path}' not found.")
        return

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = image_processing_pb2_grpc.MasterServiceStub(channel)
        try:
            response = stub.ProcessImage(image_processing_pb2.ImageRequest(image_data=image_data))
            print(f"Request submitted. Request ID: {response.request_id}")
        except grpc.RpcError as e:
            print(f"Error communicating with master: {str(e)}")


def get_result(request_id):
    """
    Fetches the result of a processed request using the request ID.
    """
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = image_processing_pb2_grpc.MasterServiceStub(channel)
        try:
            response = stub.QueryResult(image_processing_pb2.ResultRequest(request_id=request_id))
            if response.result_available:
                print(f"Result for Request ID {request_id}: {response.result}")
            else:
                print(f"Result not yet available for Request ID {request_id}.")
        except grpc.RpcError as e:
            print(f"Error fetching result: {str(e)}")


def list_models():
    """
    Lists all available models on the server.
    """
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = image_processing_pb2_grpc.MasterServiceStub(channel)
        try:
            response = stub.GetModels(image_processing_pb2.ModelRequest())
            print("Available Models:")
            for model in response.models:
                print(f"- {model}")
        except grpc.RpcError as e:
            print(f"Error fetching models: {str(e)}")


def model_details(model_name):
    """
    Fetches details of a specific model.
    """
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = image_processing_pb2_grpc.MasterServiceStub(channel)
        try:
            response = stub.GetModelDetails(image_processing_pb2.ModelDetailRequest(model_name=model_name))
            print(f"Details for Model '{model_name}':")
            print(response.details)
        except grpc.RpcError as e:
            print(f"Error fetching model details: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="Client for image recognition.")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Detect command
    detect_parser = subparsers.add_parser("detect", help="Detect objects in an image")
    detect_parser.add_argument("image_path", type=str, help="Path to the image file")

    # Result command
    result_parser = subparsers.add_parser("result", help="Fetch the result of a request")
    result_parser.add_argument("request_id", type=str, help="Request ID")

    # List models command
    subparsers.add_parser("get models", help="List all available models")

    # Model details command
    model_parser = subparsers.add_parser("model", help="Get details of a specific model")
    model_parser.add_argument("model_name", type=str, help="Name of the model")

    # Parse arguments
    args = parser.parse_args()

    # Execute commands
    if args.command == "detect":
        detect_image(args.image_path)
    elif args.command == "result":
        get_result(args.request_id)
    elif args.command == "get models":
        list_models()
    elif args.command == "model":
        model_details(args.model_name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
