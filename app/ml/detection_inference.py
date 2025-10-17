"""
Detection inference module for CADe (Computer-Aided Detection).

This module handles loading the detection model and performing
inference to detect chest X-ray findings with bounding boxes.
"""

import torch
import time
import os
from typing import List, Dict, Tuple, Optional
from app.ml.models.chest_xray_detector import ChestXRayDetector
from app.ml.preprocessing.image_processor import ImageProcessor
from app.core.config import get_settings


class DetectionInference:
    """
    Handles detection model loading and inference for chest X-ray CADe.
    
    Manages the PyTorch detection model lifecycle and provides an interface
    for detecting findings in medical images.
    
    Attributes:
        device: PyTorch device (CPU or CUDA)
        model: Loaded detection model
        processor: Image preprocessing pipeline
        finding_types: List of detectable findings
        model_loaded: Whether model is successfully loaded
        use_mock_detections: Whether to use mock detections (demo mode)
        
    Example:
        >>> detector = DetectionInference()
        >>> detector.load_model()
        >>> detections, proc_time = detector.detect("xray.png")
        >>> for det in detections:
        >>>     print(f"{det['finding_type']}: {det['confidence']:.2%}")
    """
    
    def __init__(self, confidence_threshold: float = 0.5):
        """
        Initialize the detection inference engine.
        
        Args:
            confidence_threshold: Minimum confidence for detections (0.0 to 1.0)
        """
        self.settings = get_settings()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[ChestXRayDetector] = None
        self.processor = ImageProcessor()
        self.confidence_threshold = confidence_threshold
        self.finding_types = ChestXRayDetector.FINDING_TYPES
        self.model_loaded = False
        self.use_mock_detections = True  # Default to mock for demo
        
        print(f"Detection device: {self.device}")
    
    def load_model(self, model_path: Optional[str] = None) -> None:
        """
        Load the detection model from disk.
        
        Loads trained model weights if available, otherwise uses
        placeholder model with mock detections for demonstration.
        
        Args:
            model_path: Path to detection model weights (optional)
            
        Raises:
            Exception: If there's an error loading the model
        """
        try:
            # Initialize model architecture
            self.model = ChestXRayDetector(
                num_classes=len(self.finding_types),
                confidence_threshold=self.confidence_threshold
            )
            
            # Determine model path
            if model_path is None:
                # Check for detection model in ml_models directory
                detection_model_path = os.path.join(
                    os.path.dirname(self.settings.model_path),
                    "chest_xray_detector.pth"
                )
            else:
                detection_model_path = model_path
            
            # Load trained weights if available
            if os.path.exists(detection_model_path):
                self.model.load_weights(detection_model_path)
                self.use_mock_detections = False
                print(f"✓ Detection model loaded from {detection_model_path}")
            else:
                print(f"⚠ Warning: Detection model not found at {detection_model_path}")
                print("  Using mock detections for demonstration purposes")
                print("  Train and save a detection model to enable real detections")
                self.use_mock_detections = True
            
            # Move model to device and set to evaluation mode
            self.model.to(self.device)
            self.model.eval()
            self.model_loaded = True
            
        except Exception as e:
            print(f"✗ Error loading detection model: {str(e)}")
            self.model_loaded = False
            raise
    
    def detect(
        self, 
        image_path: str
    ) -> Tuple[List[Dict[str, any]], float]:
        """
        Detect findings in a chest X-ray image.
        
        Processes the image and runs detection to identify findings
        with bounding boxes and confidence scores.
        
        Args:
            image_path: Path to the chest X-ray image or DICOM file
            
        Returns:
            Tuple containing:
                - detections (list): List of detected findings, each with:
                    - finding_type (str): Type of finding
                    - confidence (float): Confidence score (0-1)
                    - bbox (list): Bounding box [x1, y1, x2, y2] (normalized)
                - processing_time (float): Time taken for detection in seconds
                
        Raises:
            RuntimeError: If model is not loaded
            FileNotFoundError: If image file doesn't exist
            
        Example:
            >>> detections, time = detector.detect("xray.png")
            >>> print(f"Found {len(detections)} findings in {time:.3f}s")
            >>> for det in detections:
            >>>     print(f"  - {det['finding_type']}: {det['confidence']:.2%}")
            >>>     print(f"    BBox: {det['bbox']}")
        """
        if not self.model_loaded:
            print("Detection model not loaded, attempting to load...")
            self.load_model()
        
        if self.model is None:
            raise RuntimeError("Detection model failed to load")
        
        start_time = time.time()
        
        # Preprocess image
        image_tensor = self.processor.process_image(image_path)
        image_tensor = image_tensor.to(self.device)
        
        # Run detection
        detections = self.model.detect(
            image_tensor, 
            return_mock=self.use_mock_detections
        )
        
        processing_time = time.time() - start_time
        
        return detections, processing_time
    
    def detect_batch(
        self,
        image_paths: List[str]
    ) -> Tuple[List[List[Dict[str, any]]], float]:
        """
        Detect findings in multiple chest X-ray images.
        
        Args:
            image_paths: List of paths to image or DICOM files
            
        Returns:
            Tuple containing:
                - batch_detections (list): List of detection lists (one per image)
                - total_processing_time (float): Total time for batch
                
        Raises:
            RuntimeError: If model is not loaded
        """
        if not self.model_loaded:
            print("Detection model not loaded, attempting to load...")
            self.load_model()
        
        if self.model is None:
            raise RuntimeError("Detection model failed to load")
        
        start_time = time.time()
        batch_detections = []
        
        for image_path in image_paths:
            try:
                detections, _ = self.detect(image_path)
                batch_detections.append(detections)
            except Exception as e:
                print(f"Error processing {image_path}: {str(e)}")
                batch_detections.append([])
        
        total_processing_time = time.time() - start_time
        
        return batch_detections, total_processing_time
    
    def set_confidence_threshold(self, threshold: float) -> None:
        """
        Update the confidence threshold for detections.
        
        Args:
            threshold: New confidence threshold (0.0 to 1.0)
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
        
        self.confidence_threshold = threshold
        if self.model is not None:
            self.model.confidence_threshold = threshold
