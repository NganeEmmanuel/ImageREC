import asyncio
import os
import time
import grpc
import json
from uuid import uuid4
import warnings

from CloudServer.database_manager import database_handler, auth
from CloudServer.description_generator.description_generator import generate_descriptions
from CloudServer.processImages.process_image import process_image
import image_processing_pb2
import image_processing_pb2_grpc
from CloudServer.virtualization.datacenter import Datacenter
from CloudServer.virtualization.host import Host
from CloudServer.worker_manager.scale_worker import scale_workers, monitor_workers
from CloudServer.state_manager.shared_request_state import SharedState
from CloudServer.state_manager.shared_worker_state import SharedWorkerState
from CloudServer.virtualization.virtual_machine import VirtualMachine

# initialize state manager classes for request and worker
shared_request_state = SharedState()
shared_worker_state = SharedWorkerState()

# Define the directory for saving images
IMAGE_STORAGE_DIR = os.path.join(os.getcwd(), "images")

available_models = {
    "Yolov5s": {
        "description": "YOLOv5 is a computer vision model that is used for object detection. It is an enhanced "
                       "version of previous YOLO models and operates at a high inference speed, making it effective "
                       "for real-time applications. It uses PyTorch for faster and more accurate deployment.",
        "accuracy": 0.85,
    },
}

warnings.filterwarnings("ignore", category=FutureWarning)


class MasterServiceServicer(image_processing_pb2_grpc.MasterServiceServicer):
    def __init__(self):
        self.workers = {}

    def ProcessImage(self, request, context):
        # Run the async function in the event loop
        return asyncio.run(self._process_image_async(request, context))

    async def _process_image_async(self, request, context):
        user_credentials = request.user

        # Authenticate user before adding request to queue or processing
        if not auth.authenticate_user(
                user_credentials.username, user_credentials.email, user_credentials.password
        ):
            print("Authentication failed. Request denied.")
            return image_processing_pb2.ProcessImageResponse(request_id="Cannot authorize user")

        return await process_image(shared_request_state, request, context)

    def ReprocessImage(self, request, context):
        # Extract request details
        request_id = request.request_id
        user_credentials = request.user

        # Authenticate the user
        if not auth.authenticate_user(
                user_credentials.username, user_credentials.email, user_credentials.password
        ):
            return image_processing_pb2.ReprocessResultResponse(
                status="failed",
                message=f"Authentication failed for user: {user_credentials.email}",
                request_id=""
            )

        # Get Request from the database
        saved_request = database_handler.get_request(request_id, user_credentials.email)

        # Locate the image in the filesystem
        # todo Update so that images are looked up based on the fact that their names contains the request_id
        # todo This is because some request can have multiple images and the image name will be the (requestid_imageid.jpg)
        raw_image_path = os.path.join(IMAGE_STORAGE_DIR, f"{request_id}.jpg")
        image_path = os.path.normpath(raw_image_path)  # Normalize the path to handle extra slashes
        if not os.path.exists(image_path):
            return image_processing_pb2.ReprocessResultResponse(
                status="failed",
                message=f"No existing request found with ID: {request_id}",
                request_id=""

            )

        # Read the image and convert it to bytes
        try:
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
        except Exception as e:
            print(f"Failed to read image: {e}")
            return image_processing_pb2.ReprocessResultResponse(
                status="failed",
                message="Error occurred while reading the stored image.",
                request_id=""
            )

        # Add the reprocessing request to the queue
        new_request_id = str(uuid4())  # Create a new request ID for tracking
        with shared_request_state.state_lock:
            shared_request_state.request_state[new_request_id] = {"status": "pending", "result": None}
        shared_request_state.request_queue.put((new_request_id, image_data, user_credentials))

        # Add the reprocess request to the database
        database_handler.add_request(
            new_request_id, user_credentials.email, saved_request.model_name, saved_request.action_type
        )
        print(f"Reprocessing request {new_request_id} added to the queue.")

        return image_processing_pb2.ReprocessResultResponse(
            status="success",
            message="",
            request_id=new_request_id
        )

    def QueryResult(self, request, context):
        request_id = request.request_id

        # If not in memory, check the database
        try:
            result = database_handler.get_result_by_request_id(request_id)
            if result:
                return image_processing_pb2.ResultResponse(status="completed", result_data=result)
            else:
                return image_processing_pb2.ResultResponse(status="not_found", result_data="Request ID not found.")
        except Exception as e:
            print(f"Error retrieving result from database for Request ID {request_id}: {e}")
            return image_processing_pb2.ResultResponse(status="error",
                                                       result_data="An error occurred while fetching the result.")

    def HealthCheck(self, request, context):
        return image_processing_pb2.HealthResponse(status="ready")

    def GetAllUserRequest(self, request, context):
        """
        Fetches all requests made by the user from the database and streams them back.

        Args:
            request: Contains user credentials for authentication (email, username, password).
            context: gRPC context for handling errors and metadata.

        Yields:
            RequestDataRespond: A stream of user requests.
        """
        try:
            # Validate user credentials
            if not auth.authenticate_user(request.username, request.email, request.password):
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                context.set_details("Invalid user credentials.")
                return

            # Fetch user requests from the database
            user_requests = database_handler.get_all_requests(request.email)

            # Stream each request back to the client
            for user_request in user_requests:
                yield image_processing_pb2.RequestDataRespond(
                    request_id=user_request['request_id'],
                    request_status=user_request['status'],
                    request_date=user_request['request_date'].strftime("%Y-%m-%d %H:%M:%S") if user_request[
                        'request_date'] else "N/A",
                )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to fetch user requests: {str(e)}")

    def DeleteProcessingRequest(self, request, context):
        """
        Deletes a request and all associated results from the database.

        Args:
            request: Contains user credentials and the request ID to delete.
            context: gRPC context for handling errors and metadata.

        Returns:
            ImageResponse: Indicates success or failure of the deletion.
        """
        try:
            # Validate user credentials
            if not auth.authenticate_user(request.user.username, request.user.email, request.user.password):
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                context.set_details("Invalid user credentials.")
                return image_processing_pb2.ProcessImageResponse(request_id=request.request_id)

            # Delete the request from the database
            is_deleted = database_handler.delete_request(request.request_id, request.user.email)
            print(f"is deleted: {is_deleted}")
            if is_deleted:
                return image_processing_pb2.ProcessImageResponse(request_id=request.request_id)
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Request ID not found or you do not have permission to delete it.")
                return image_processing_pb2.ProcessImageResponse(request_id=request.request_id)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to delete the request: {str(e)}")
            return image_processing_pb2.ProcessImageResponse(request_id=request.request_id)

    def GetModels(self, request, context):
        for model_name, model_info in available_models.items():
            yield image_processing_pb2.ModelInfo(
                model_name=model_name,
                description=model_info["description"],
                accuracy=model_info["accuracy"],
            )


# Threads
async def async_process_requests(shared_state, shared_worker_state):
    while True:
        try:
            # Dequeue the next request
            request_id, processed_images, model_requested, action_type, user_email = await asyncio.wait_for(
                shared_state.request_queue.get(), timeout=10
            )
        except asyncio.TimeoutError:
            continue

        print(f"Processing request {request_id}...")

        # Determine required number of workers
        required_workers = max(
            shared_worker_state.MIN_WORKERS,
            min(shared_worker_state.MAX_WORKERS, shared_state.request_queue.qsize()),
        )
        print(
            f"Scaling workers. Current: {len(shared_worker_state.worker_registry)}, Required: {required_workers}"
        )
        scale_workers(shared_worker_state, required_workers, model_requested, action_type)

        all_detections = []

        for image_data in processed_images:
            worker_count = 0
            while (
                worker_count < len(shared_worker_state.worker_registry)
                and not shared_worker_state.available_workers.empty()
            ):
                worker_address = shared_worker_state.available_workers.get()
                print(f"Assigning task to worker {worker_address}...")

                try:
                    with grpc.insecure_channel(worker_address) as channel:
                        stub = image_processing_pb2_grpc.WorkerServiceStub(channel)
                        response = stub.ProcessChunk(
                            image_processing_pb2.ChunkRequest(
                                chunk_data=image_data["image_bytes"], action_type=action_type
                            )
                        )
                        print(f"Worker {worker_address} processed chunk successfully.")

                        # Ensure response is treated as a string
                        if isinstance(response.result, str):
                            try:
                                result_data = json.loads(response.result)  # Convert string to dictionary
                                all_detections.append(result_data)
                            except json.JSONDecodeError:
                                print(f"Failed to parse JSON response from worker {worker_address}: {response.result}")
                        else:
                            print(f"Unexpected response format from worker {worker_address}: {response.result}")

                        with shared_worker_state.worker_lock:
                            shared_worker_state.worker_registry[worker_address]["last_active"] = time.time()
                        shared_worker_state.available_workers.put(worker_address)
                    worker_count += 1
                except Exception as e:
                    print(f"Worker {worker_address} failed: {e}")

        # Ensure valid detections before generating descriptions
        if not all_detections:
            print(f"Warning: No detections were received for request {request_id}.")
            descriptions = []
        else:
            descriptions = [generate_descriptions(json.dumps(det)) for det in all_detections]

        # Store result in the database
        database_handler.add_result(request_id, json.dumps(descriptions), user_email)
        database_handler.update_request_status(request_id, "Success")

        async with shared_state.state_lock:
            shared_state.request_state[request_id] = {"status": "completed", "result": descriptions}

        print(f"Request {request_id} processed with {len(all_detections)} detections.")
        shared_state.request_queue.task_done()


def process_requests():
    print("process_requests function started...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(async_process_requests(shared_request_state, shared_worker_state))


def serve():
    # Initialize Datacenter
    datacenter = Datacenter(datacenter_id=1)
    print("Datacenter 1 initialized.")

    # Initialize Hosts and Assign to Datacenter
    master_host = Host(host_id=1, os="Linux", arch="x86_64", cpu=128, ram_capacity=128)
    worker_host = Host(host_id=2, os="Linux", arch="x86_64", cpu= 128, ram_capacity=128)
    datacenter.add_host(master_host)
    print("Host 1 initialized and assigned to Datacenter 1.")
    datacenter.add_host(worker_host)
    print("Host 2 initialized and assigned to Datacenter 1.")

    # Register the worker_hosts in the worker_host_registry
    shared_worker_state.worker_host_registry[worker_host.host_id] = {
        "worker_host" : worker_host,
        "status" : "Healthy"
    }
    shared_worker_state.available_workers.put(worker_host.host_id)

    # Initialize and start the Master VM within the master host
    master_vm = VirtualMachine("master", "master_vm", ram=16, cpu=4, storage=100)
    master_host.allocate_vm(master_vm)
    master_vm.start_vm()

    # Launch the Master gRPC Server application inside Master VM
    master_vm.run_master_application(
        auto_scaling_process=monitor_workers,
        request_process=process_requests,
        service_servicer_class=MasterServiceServicer,
        shared_worker_state=shared_worker_state,
        app_name="master_VM",
        port=50051
    )

    print("Master gRPC server application is running inside the master VM.")


if __name__ == "__main__":
    serve()
