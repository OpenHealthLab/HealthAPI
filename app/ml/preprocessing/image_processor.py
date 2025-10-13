
from PIL import Image
import torch
from torchvision import transforms
import numpy as np

class ImageProcessor:
    def __init__(self, img_size=224):
        self.img_size = img_size
        self.transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.Grayscale(num_output_channels=1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485], std=[0.229])
        ])
    
    def process_image(self, image_path: str) -> torch.Tensor:
        """Process image for model input"""
        try:
            image = Image.open(image_path).convert('RGB')
            tensor = self.transform(image)
            return tensor.unsqueeze(0)
        except Exception as e:
            raise ValueError(f"Error processing image: {str(e)}")
    
    def validate_image(self, image_path: str) -> bool:
        """Validate image format and size"""
        try:
            image = Image.open(image_path)
            if image.format not in ['PNG', 'JPEG', 'JPG']:
                return False
            return True
        except:
            return False

