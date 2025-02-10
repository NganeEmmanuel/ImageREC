import torch
import torch.nn as nn
import torchvision.models as models


def create_model(num_classes):
    """
    Create a DenseNet model for melanoma classification.

    Args:
        num_classes (int): Number of output classes.

    Returns:
        nn.Module: DenseNet model.
    """
    model = models.densenet121(pretrained=True)
    model.classifier = nn.Sequential(
        nn.Linear(model.classifier.in_features, 512),
        nn.ReLU(),
        nn.Dropout(0.4),
        nn.Linear(512, num_classes)
    )
    return model
