import torch.nn as nn
import torch.nn.functional as F


class MelanomaModel(nn.Module):
    def __init__(self):
        super(MelanomaModel, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, stride=1, padding=1)
        self.fc1 = nn.Linear(32 * 256 * 256, 3)  # Output for 3 classes

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = x.view(x.size(0), -1)  # Flatten the tensor
        x = self.fc1(x)
        return x
