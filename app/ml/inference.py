
import torch
import time
from typing import Tuple, Dict
from app.ml.models.chest_xray_model import ChestXRayModel
from app.ml.preprocessing.image_processor import ImageProcessor
from app.core.config import get_settings
import os

class ModelInference:
    def __init__(self):
        self.settings = get_settings()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.processor = ImageProcessor()
        self.classes = ["Normal", "Pneumonia", "COVID-19"]
        self.model_loaded = False
        
    def load_model(self):
        """Load the PyTorch model"""
        try:
            self.model = ChestXRayModel(num_classes=len(self.classes))
            
            if os.path.exists(self.settings.model_path):
                self.model.load_state_dict(torch.load(
                    self.settings.model_path,
                    map_location=self.device
                ))
                print(f"Model loaded from {self.settings.model_path}")
            else:
                print(f"Warning: Model file not found at {self.settings.model_path}")
                print("Using untrained model for demonstration")
            
            self.model.to(self.device)
            self.model.eval()
            self.model_loaded = True
            
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            self.model_loaded = False
            raise
    
    def predict(self, image_path: str) -> Tuple[str, float, float, Dict]:
        """
        Make prediction on chest X-ray image
        Returns: (predicted_class, confidence, processing_time, all_probabilities)
        """
        if not self.model_loaded:
            self.load_model()
        
        start_time = time.time()
        
        # Preprocess image
        image_tensor = self.processor.process_image(image_path)
        image_tensor = image_tensor.to(self.device)
        
        # Inference
        with torch.no_grad():
            outputs = self.model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probabilities, 1)
        
        processing_time = time.time() - start_time
        
        predicted_class = self.classes[predicted.item()]
        confidence_score = confidence.item()
        
        all_probs = {
            self.classes[i]: float(probabilities[0][i])
            for i in range(len(self.classes))
        }
        
        return predicted_class, confidence_score, processing_time, all_probs

