import torch
import torchvision

faster_rcnn = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)