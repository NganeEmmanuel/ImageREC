import os
import json
import argparse
import grpc
import configparser
import image_processing_pb2
import image_processing_pb2_grpc
from tabulate import tabulate
from urllib.parse import urlparse

CONFIG_FILE = "auth_config.ini"


def initialize_config():
    """
    Initializes the configuration file if it doesn't exist.
    """
    config = configparser.ConfigParser()
    if not config.read(CONFIG_FILE):  # Check if the file exists and can be read
        config['User'] = {
            'username': '',
            'email': '',
            'password': ''
        }
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)


def configure_user(username=None, email=None, password=None):
    """
    Configures the user credentials in the configuration file.
    """
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    if 'User' not in config:
        config['User'] = {}

    if username:
        config['User']['username'] = username
    if email:
        config['User']['email'] = email
    if password:
        config['User']['password'] = password

    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

    print("User configuration updated successfully.")


def get_user_credentials():
    """
    Reads user credentials from the configuration file.
    """
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    if 'User' not in config:
        raise ValueError("User credentials are not configured. Please configure them using the 'configure' command.")

    return image_processing_pb2.UserCredentials(
        username=config['User']['username'],
        email=config['User']['email'],
        password=config['User']['password']
    )


def is_remote_image(path):
    """Determine if the given path is a URL."""
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def read_local_image(image_path):
    """Read a local image file and return its binary data."""
    try:
        with open(image_path, 'rb') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File '{image_path}' not found.")
        return None


def parse_image_paths(image_paths):
    """Parse image paths and return a list of ImageData messages."""
    images = []
    image_id = 1
    for path in image_paths:
        if is_remote_image(path):
            images.append(image_processing_pb2.ImageData(image_id=image_id, image_url=path, location="remote"))
        else:
            image_data = read_local_image(path)
            if image_data:
                images.append(image_processing_pb2.ImageData(image_id=image_id, image_data=image_data, location="local"))
        image_id += 1
    return images


def process_image(args):
    """Send a request to process images."""
    image_paths = []
    json_user_credentials = None

    if args.image_path:
        image_paths = [args.image_path]
    elif args.json_file:
        with open(args.json_file, 'r') as f:
            data = json.load(f)
            image_paths = [img.get('image_url') for img in data.get('images', [])]
            args.model_name = data.get('model', args.model_name)
            args.action_type = data.get('action_type', args.action_type)
            # Extract user credentials from JSON if present
            if 'username' in data and 'email' in data and 'password' in data:
                json_user_credentials = {
                    'username': data['username'],
                    'email': data['email'],
                    'password': data['password']
                }

    # Parse images into ImageData messages
    images = parse_image_paths(image_paths)
    if not images:
        print("Error: No valid images found.")
        return

    # Use credentials from JSON if available, otherwise use config file
    user_credentials = json_user_credentials or get_user_credentials()

    # Build request
    request = image_processing_pb2.ProcessImageRequest(
        user=user_credentials,
        images=images,
        model_name=args.model_name,
        action_type=args.action_type,
        number_of_remote_images=sum(1 for img in images if img.location == "remote")
    )

    # Send request
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = image_processing_pb2_grpc.MasterServiceStub(channel)
        try:
            response = stub.ProcessImage(request)
            print(f"Request submitted. Request ID: {response.request_id}")
        except grpc.RpcError as e:
            print(f"Error communicating with master: {str(e)}")




def detect_remote_image(image_url):
    """
    Sends a remote image URL to the master for processing and returns a request ID.
    """
    user_credentials = get_user_credentials()

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = image_processing_pb2_grpc.MasterServiceStub(channel)
        try:
            response = stub.ProcessRemoteImage(
                image_processing_pb2.RemoteImageRequest(user=user_credentials, image_url=image_url)
            )
            print(f"Request submitted for remote image. Request ID: {response.request_id}")
        except grpc.RpcError as e:
            print(f"Error communicating with master: {str(e)}")


def get_result(request_id):
    """
    Fetches the result of a processed request using the request ID.
    """
    user_credentials = get_user_credentials()

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = image_processing_pb2_grpc.MasterServiceStub(channel)
        try:
            response = stub.QueryResult(
                image_processing_pb2.QueryRequest(user=user_credentials, request_id=request_id)
            )
            if response.status == "completed":
                print(f"Result for Request ID {request_id}: {response.result_data}")
            else:
                print(f"Request ID {request_id} is still processing. Status: {response.status}")
        except grpc.RpcError as e:
            print(f"Error fetching result: {str(e)}")


def get_all_user_requests():
    user_credentials = get_user_credentials()

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = image_processing_pb2_grpc.MasterServiceStub(channel)
        try:
            responses = stub.GetAllUserRequest(
                image_processing_pb2.UserCredentials(username=user_credentials.username, email=user_credentials.email, password=user_credentials.password)
            )
            data = []
            for response in responses:
                data.append([response.request_id, response.request_status, response.request_date])

            if data:
                print(tabulate(data, headers=["Request ID", "Status", "Request Date"], tablefmt="grid"))
            else:
                print("No requests found.")
        except grpc.RpcError as e:
            print(f"Error fetching user requests: {str(e)}")


def delete_processing_request(request_id):
    user_credentials = get_user_credentials()

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = image_processing_pb2_grpc.MasterServiceStub(channel)
        try:
            response = stub.DeleteProcessingRequest(
                image_processing_pb2.QueryRequest(
                    user=user_credentials,
                    request_id=request_id
                )
            )
            print(f"Request ID {request_id} deleted successfully.")
        except grpc.RpcError as e:
            print(f"Error deleting request: {str(e)}")


def list_models():
    """
    Lists all available models on the server.
    """
    user_credentials = get_user_credentials()

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = image_processing_pb2_grpc.MasterServiceStub(channel)
        try:
            response = stub.GetModels(
                image_processing_pb2.ModelRequest(user=user_credentials)
            )
            print("Available Models:")
            for model in response.models:
                print(f"- {model}")
        except grpc.RpcError as e:
            print(f"Error fetching models: {str(e)}")


def model_details(model_name):
    """
    Fetches details of a specific model.
    """
    user_credentials = get_user_credentials()

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = image_processing_pb2_grpc.MasterServiceStub(channel)
        try:
            response = stub.GetModelDetails(
                image_processing_pb2.ModelDetailRequest(user=user_credentials, model_name=model_name)
            )
            print(f"Details for Model '{model_name}':")
            print(response.details)
        except grpc.RpcError as e:
            print(f"Error fetching model details: {str(e)}")


def reprocess_request(request_id):
    """
    Sends a reprocessing request for an existing image.
    """
    user_credentials = get_user_credentials()

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = image_processing_pb2_grpc.MasterServiceStub(channel)
        try:
            response = stub.ReprocessImage(
                image_processing_pb2.ReprocessRequest(user=user_credentials, request_id=request_id)
            )
            if response.status == "success":
                print(f"Reprocessing initiated. New Request ID: {response.request_id}")
            else:
                print(f"Reprocessing failed: {response.request_id}")
        except grpc.RpcError as e:
            print(f"Error communicating with master: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="Client for image recognition.")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Configure user command
    configure_parser = subparsers.add_parser("configure", help="Configure user credentials")
    configure_parser.add_argument("-u", "--username", type=str, help="Username")
    configure_parser.add_argument("-e", "--email", type=str, help="Email")
    configure_parser.add_argument("-p", "--password", type=str, help="Password")

    # Detect command
    detect_parser = subparsers.add_parser("detect", help="Process images")
    detect_parser.add_argument("image_path", nargs="?", type=str, help="Path to the image file")
    detect_parser.add_argument("-r", "--remote", type=str, help="URL of the remote image")
    detect_parser.add_argument("-j", "--json_file", type=str, help="Path to a JSON file with request details")
    detect_parser.add_argument("-t", "--text_file", type=str, help="Path to a text file with image paths")
    detect_parser.add_argument("--model_name", type=str, required=True, help="Name of the model to use")
    detect_parser.add_argument("--action_type", type=str, required=True, help="Action to perform (e.g., categorize, count_objects)")

    # Result command
    result_parser = subparsers.add_parser("result", help="Fetch the result of a request")
    result_parser.add_argument("request_id", type=str, help="Request ID")

    # List models command
    subparsers.add_parser("get_models", help="List all available models")

    # Model details command
    model_parser = subparsers.add_parser("model", help="Get details of a specific model")
    model_parser.add_argument("model_name", type=str, help="Name of the model")

    # Reprocess command
    reprocess_parser = subparsers.add_parser("reprocess", help="Reprocess an existing request")
    reprocess_parser.add_argument("request_id", type=str, help="Request ID to reprocess")

    # Get requests command
    subparsers.add_parser("get_requests", help="List all user requests")

    # Delete request command
    delete_parser = subparsers.add_parser("delete_request", help="Delete a specific user request")
    delete_parser.add_argument("request_id", type=str, help="Request ID to delete")

    # Parse arguments
    args = parser.parse_args()

    if args.command == "configure":
        configure_user(username=args.username, email=args.email, password=args.password)
    elif args.command == "detect":
        process_image(args)
    elif args.command == "result":
        get_result(args.request_id)
    elif args.command == "get_requests":
        get_all_user_requests()
    elif args.command == "delete_request":
        delete_processing_request(args.request_id)
    elif args.command == "get_models":
        list_models()
    elif args.command == "model":
        model_details(args.model_name)
    elif args.command == "reprocess":
        reprocess_request(args.request_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
