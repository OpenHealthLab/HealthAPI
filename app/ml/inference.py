"""
Machine learning model inference module.

This module handles loading the trained PyTorch model and
performing inference on chest X-ray images.
"""

import torch
import time
import os
from typing import Tuple, Dict, Optional
from app.ml.models.chest_xray_model import ChestXRayModel
from app.ml.preprocessing.image_processor import ImageProcessor
from app.core.config import get_settings


class ModelInference:
    """
    Handles ML model loading and inference for chest X-ray classification.
    
    This class manages the PyTorch model lifecycle and provides a simple
    interface for making predictions on medical images.
    
    Attributes:
        device: PyTorch device (CPU or CUDA)
        model: Loaded PyTorch model
        processor: Image preprocessing pipeline
        classes: List of prediction classes
        model_loaded: Whether model is successfully loaded
        
    Example:
        >>> inference = ModelInference()
        >>> inference.load_model()
        >>> pred_class, confidence, time, probs = inference.predict("xray.png")
        >>> print(f"Prediction: {pred_class} ({confidence:.2%})")
    """
    
    def __init__(self):
        """Initialize the inference engine."""
        self.settings = get_settings()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[ChestXRayModel] = None
        self.processor = ImageProcessor()
        self.classes = ["Normal", "Pneumonia", "COVID-19"]
        self.model_loaded = False
        
        print(f"Inference device: {self.device}")
        
    def load_model(self) -> None:
        """
        Load the PyTorch model from disk.
        
        Loads the trained model weights and prepares the model for inference.
        If the model file doesn't exist, initializes an untrained model
        for demonstration purposes.
        
        Raises:
            Exception: If there's an error loading the model
            
        Note:
            In production, you should ensure the model file exists
            before starting the application.
        """
        try:
            # Initialize model architecture
            self.model = ChestXRayModel(num_classes=len(self.classes))
            
            # Load trained weights if available
            if os.path.exists(self.settings.model_path):
                self.model.load_state_dict(torch.load(
                    self.settings.model_path,
                    map_location=self.device
                ))
                print(f"✓ Model loaded from {self.settings.model_path}")
            else:
                print(f"⚠ Warning: Model file not found at {self.settings.model_path}")
                print("  Using untrained model for demonstration purposes")
                print("  Please train a model and save it to the specified path")
            
            # Move model to device and set to evaluation mode
            self.model.to(self.device)
            self.model.eval()
            self.model_loaded = True
            
        except Exception as e:
            print(f"✗ Error loading model: {str(e)}")
            self.model_loaded = False
            raise
    
    def predict(self, image_path: str) -> Tuple[str, float, float, Dict[str, float]]:
        """
        Make prediction on a chest X-ray image.
        
        Processes the image and runs it through the model to get predictions
        for all classes along with confidence scores.
        
        Args:
            image_path: Path to the chest X-ray image file
            
        Returns:
            Tuple containing:
                - predicted_class (str): The predicted class name
                - confidence (float): Confidence score for predicted class (0-1)
                - processing_time (float): Time taken for inference in seconds
                - all_probabilities (dict): Probabilities for all classes
                
        Raises:
            RuntimeError: If model is not loaded
            FileNotFoundError: If image file doesn't exist
            
        Example:
            >>> pred_class, conf, time, probs = inference.predict("xray.png")
            >>> print(f"Prediction: {pred_class}")
            >>> print(f"Confidence: {conf:.2%}")
            >>> print(f"Processing time: {time:.3f}s")
            >>> print(f"All probabilities: {probs}")
        """
        if not self.model_loaded:
            print("Model not loaded, attempting to load...")
            self.load_model()
        
        if self.model is None:
            raise RuntimeError("Model failed to load")
        
        start_time = time.time()
        
        # Preprocess image
        image_tensor = self.processor.process_image(image_path)
        image_tensor = image_tensor.to(self.device)
        
        # Run inference
        with torch.no_grad():
            outputs = self.model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probabilities, 1)
        
        processing_time = time.time() - start_time
        
        # Extract results
        predicted_class = self.classes[predicted.item()]
        confidence_score = confidence.item()
        
        # Get probabilities for all classes
        all_probs = {
            self.classes[i]: float(probabilities[0][i])
            for i in range(len(self.classes))
        }
        
        return predicted_class, confidence_score, processing_time, all_probs
