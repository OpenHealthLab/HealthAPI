import torch
import torch.nn as nn
from torchvision import models

class ChestXRayModel(nn.Module):
    def __init__(self, num_classes=3):
        super(ChestXRayModel, self).__init__()
        # Using ResNet18 as base model
        self.model = models.resnet18(pretrained=False)
        
        # Modify first conv layer to accept grayscale images
        self.model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
        
        # Modify final layer for our classes
        num_features = self.model.fc.in_features
        self.model.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(num_features, num_classes)
        )
        
    def forward(self, x):
        return self.model(x)

