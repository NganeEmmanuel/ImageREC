import argparse
import grpc
import configparser
import image_processing_pb2
import image_processing_pb2_grpc

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

    user_credentials = get_user_credentials()

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = image_processing_pb2_grpc.MasterServiceStub(channel)
        try:
            response = stub.ProcessImage(
                image_processing_pb2.ImageRequest(user=user_credentials, image_data=image_data)
            )
            print(f"Request submitted. Request ID: {response.request_id}")
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
                print(f"Result for Request ID {request_id}: {response.result}")
            else:
                print(f"Request ID {request_id} is still processing. Status: {response.status}")
        except grpc.RpcError as e:
            print(f"Error fetching result: {str(e)}")


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


def main():
    parser = argparse.ArgumentParser(description="Client for image recognition.")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Configure user command
    configure_parser = subparsers.add_parser("configure", help="Configure user credentials")
    configure_parser.add_argument("-u", "--username", type=str, help="Username")
    configure_parser.add_argument("-e", "--email", type=str, help="Email")
    configure_parser.add_argument("-p", "--password", type=str, help="Password")

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

    if args.command == "configure":
        configure_user(username=args.username, email=args.email, password=args.password)
    elif args.command == "detect":
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
