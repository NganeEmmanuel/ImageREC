import os

# Models directory (Assumed to store model files)
MODELS_DIR = os.path.join(os.getcwd(), "CloudServer/models")


def get_model_path(model_name):
    """
    Retrieve the path of the model based on the requested service.
    """
    if model_name.lower() in ["yolov5", "yolov8", "melanoma_model"]:
        model_path = os.path.join(MODELS_DIR, f"{get_model_name(model_name.lower())}.pt")  # Assuming model files have .pt extension
        if os.path.exists(model_path):
            return model_path
        raise FileNotFoundError(f"Model for service '{model_name}' not found at {model_path}")

    return model_name


def get_model_name(model_requested):
    if model_requested == "yolov5":
        return "yolov5s"
    elif model_requested == "yolov8":
        return "yolov8"
    elif model_requested == "melanoma_model":
        return "melanoma_model"
    else:
        return model_requested
    # continue to include all models
