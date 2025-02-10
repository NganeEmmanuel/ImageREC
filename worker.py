import sys
import grpc
import json
from concurrent import futures

import torch
import torchvision
from torch.nn.functional import softmax
from PIL import Image
import io
import time
from torchvision.transforms import functional as f
import torchvision.transforms as transforms

import image_processing_pb2
import image_processing_pb2_grpc
from CloudServer.model_training.melanoma_model import create_model


def detect_objects(self, request, context):
    """
    General object detection in images using the loaded model.
    Args:
        request: ChunkRequest containing chunk data.
        context: gRPC context.

    Returns:
        ChunkResponse with detection results.
    """

    try:
        # Load image from the received bytes
        image_data = request.chunk_data
        image = Image.open(io.BytesIO(image_data))

        # Use YOLOv5 to process the image
        results = self.model(image)
        detections = results.pandas().xyxy[0].to_dict(orient="records")

        # Return results as JSON
        result_json = json.dumps(detections)
        return image_processing_pb2.ChunkResponse(result=result_json, worker_id=self.worker_id)

    except Exception as e:
        error_msg = f"Error processing chunk: {e}"
        context.set_details(error_msg)
        context.set_code(grpc.StatusCode.INTERNAL)
        return image_processing_pb2.ChunkResponse(result="{}", worker_id=self.worker_id)


def detect_melanoma(self, request, context):
    """
    Melanoma detection in images using the specialized melanoma model.
    Args:
        request: ChunkRequest containing chunk data.
        context: gRPC context.

    Returns:
        ChunkResponse with melanoma diagnosis results.
    """
    try:
        # Load image from the received bytes
        image_data = request.chunk_data
        image = Image.open(io.BytesIO(image_data))

        # Preprocess the image (resize, normalize, etc., as needed)
        image_tensor = preprocess_image_for_melanoma(image)
        print("Image tensor shape:", image_tensor.shape)

        # Set the model to evaluation mode
        # self.melanoma_model.eval()

        # Perform inference
        with torch.no_grad():
            outputs = self.melanoma_model(image_tensor)

        # Interpret the model's output
        diagnosis = interpret_melanoma_results(outputs)

        # Return the diagnosis as JSON
        diagnosis_json = json.dumps(diagnosis)
        print("Diagnosis:", diagnosis_json)
        return image_processing_pb2.ChunkResponse(result=diagnosis_json, worker_id=self.worker_id)

    except Exception as e:
        error_msg = f"Error processing melanoma detection: {e}"
        context.set_details(error_msg)
        context.set_code(grpc.StatusCode.INTERNAL)
        return image_processing_pb2.ChunkResponse(result="{}", worker_id=self.worker_id)


def preprocess_image_for_melanoma(image):
    """
    Apply necessary preprocessing to the image for melanoma detection.
    Args:
        image: PIL Image object.

    Returns:
        Preprocessed image suitable for melanoma model input (PyTorch Tensor).
    """
    preprocess = transforms.Compose([
        transforms.Resize((256, 256)),  # Match the model's input size
        transforms.ToTensor(),  # Convert to PyTorch Tensor
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # Normalize using ImageNet stats
    ])
    return preprocess(image).unsqueeze(0)  # Add a batch dimension


def interpret_melanoma_results(results):
    """
    Interpret the results from the melanoma model to extract a diagnosis.
    Args:
        results: Raw results from the melanoma model.

    Returns:
        A dictionary containing the diagnosis, confidence score, and any other relevant information.
    """
    # Assuming results is a tensor with probabilities for [melanoma, nevus, seborrheic keratosis]
    probabilities = softmax(results, dim=1)  # Apply softmax to get class probabilities
    probabilities = probabilities[0].tolist()  # Convert tensor to list

    # Map class indices to labels
    classes = ['melanoma', 'nevus', 'seborrheic_keratosis']
    class_probabilities = {classes[i]: probabilities[i] for i in range(len(classes))}

    # Find the highest probability class
    predicted_class = classes[probabilities.index(max(probabilities))]
    confidence = max(probabilities)

    diagnosis = {
        "predicted_class": predicted_class,
        "confidence": confidence,
        "class_probabilities": class_probabilities
    }
    return diagnosis


def detect_defect(self, request, context):
    """
    Identifies and classifies defects in manufactured products using Faster R-CNN.

    Args:
        request: ChunkRequest containing chunk data.
        context: gRPC context.

    Returns:
        ChunkResponse with defect detection results.
    """
    try:
        # Set model to evaluation mode
        self.faster_rcnn.eval()

        # Load the image from the request
        image_data = request.chunk_data
        image = Image.open(io.BytesIO(image_data)).convert("RGB")  # Ensure the image is RGB
        image_tensor = f.to_tensor(image).unsqueeze(0)  # Add batch dimension

        # Run the image through the model
        with torch.no_grad():  # Disable gradient computation for inference
            predictions = self.faster_rcnn(image_tensor)[0]

        # Parse the predictions
        results = []
        for box, label, score in zip(predictions['boxes'], predictions['labels'], predictions['scores']):
            results.append({
                'box': box.tolist(),
                'label': int(label),
                'score': float(score)
            })

        print(f"results: {results}")

        # Serialize results to JSON
        result_json = json.dumps(results)
        return image_processing_pb2.ChunkResponse(result=result_json, worker_id=self.worker_id)
    except Exception as e:
        context.set_details(f"Error in detect_defect: {e}")
        context.set_code(grpc.StatusCode.INTERNAL)
        return image_processing_pb2.ChunkResponse(result="{}", worker_id=self.worker_id)


def detect_crop_disease(self, request, context):
    """
    Crop disease image detection using ResNet.

    Args:
        request: ChunkRequest containing chunk data.
        context: gRPC context.

    Returns:
        ChunkResponse with disease detection results.
    """
    try:
        image_data = request.chunk_data
        image = Image.open(io.BytesIO(image_data))
        image_tensor = f.to_tensor(image).unsqueeze(0)
        # Add actual crop disease detection logic here

        result_json = json.dumps({"status": "Processed"})
        return image_processing_pb2.ChunkResponse(result=result_json, worker_id=self.worker_id)
    except Exception as e:
        context.set_details(f"Error in detect_crop_disease: {e}")
        context.set_code(grpc.StatusCode.INTERNAL)
        return image_processing_pb2.ChunkResponse(result="{}", worker_id=self.worker_id)


class WorkerServiceServicer(image_processing_pb2_grpc.WorkerServiceServicer):
    """
    Implements the WorkerService, handling image processing tasks and providing health checks.
    """

    def __init__(self, worker_id, master_address, action_type, model_path):
        """
        Initialize the worker and load models as required.

        Args:
            worker_id: Unique identifier for the worker.
            master_address: Address of the master service.
            model_path: Path to the YOLOv5 model or other models.
        """
        self.worker_id = worker_id
        self.master_address = master_address
        self.model_path = model_path
        print(f"Initializing Worker {worker_id}...")

        try:
            if action_type == "detect_objects":
                print(f"Loading YOLOv5 model from {model_path}...")
                self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
            elif action_type == "detect_melanoma":
                print(f"Loading melanoma model from {model_path}...")
                # Create the model architecture with the correct number of classes (3)
                self.melanoma_model = create_model(num_classes=3)
                # Load the state dictionary
                self.melanoma_model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
                self.melanoma_model.eval()  # Set to evaluation mode
            elif action_type == "detect_defect":
                print("Loading Faster R-CNN model for defect detection...")
                self.faster_rcnn = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
            elif action_type == "detect_crop_disease":
                print("Loading ResNet model for crop disease detection...")
                self.resnet = torchvision.models.resnet18(pretrained=True)
            else:
                raise ValueError(f"Unknown action type: {action_type}")

            print(f"Worker {worker_id} initialized with model for action type: {action_type}.")
        except Exception as e:
            print(f"Error initializing worker {worker_id}: {e}")
            sys.exit(1)

    def ProcessChunk(self, request, context):
        """
        Processes a chunk of image data based on action type.

        Args:
            request: ChunkRequest containing chunk data and action type.
            context: gRPC context.

        Returns:
            ChunkResponse with the result of processing.
        """
        try:
            request_action_type = request.action_type
            if request_action_type == "detect_objects":
                return detect_objects(self, request, context)
            elif request_action_type == "detect_melanoma":
                return detect_melanoma(self, request, context)
            elif request_action_type == "detect_defect":
                return detect_defect(self, request, context)
            elif request_action_type == "detect_crop_diseases":
                return detect_crop_disease(self, request, context)
            else:
                raise ValueError(f"Unknown action_type: {action_type}")
        except Exception as e:
            context.set_details(f"Error in ProcessChunk: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return image_processing_pb2.ChunkResponse(result="{}", worker_id=self.worker_id)

    def HealthCheck(self, request, context):
        """
        Responds to health check requests.

        Args:
            request: HealthRequest (no fields required).
            context: gRPC context.

        Returns:
            HealthResponse indicating the worker's status.
        """
        return image_processing_pb2.HealthResponse(status="ready")


def serve(worker_port, worker_id, master_address, action_type, model_path):
    """
    Starts the gRPC server for the worker.

    Args:
        worker_port: Port on which the worker listens.
        worker_id: Unique identifier for the worker.
        master_address: Address of the master service.
        model_path: Path to the YOLOv5 model.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    image_processing_pb2_grpc.add_WorkerServiceServicer_to_server(
        WorkerServiceServicer(worker_id, master_address, action_type, model_path), server
    )

    server_address = f"[::]:{worker_port}"
    server.add_insecure_port(server_address)
    print(f"Worker {worker_id} started at {server_address}")
    server.start()

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print(f"Worker {worker_id} shutting down.")
        server.stop(0)


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python worker.py <port> <worker_id> <master_address> <model_path>")
        sys.exit(1)

    port = int(sys.argv[1])
    worker_id = sys.argv[2]
    master_address = sys.argv[3]
    action_type = sys.argv[4]
    model_path = sys.argv[5]
    serve(port, worker_id, master_address, action_type, model_path)
