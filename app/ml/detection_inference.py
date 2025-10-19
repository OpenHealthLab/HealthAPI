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
from app.core.logging_config import get_logger

logger = get_logger(__name__)


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
        
        logger.info(f"Initializing DetectionInference on device: {self.device}")
        logger.debug(f"Confidence threshold: {confidence_threshold}")
    
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
            logger.info("Loading detection model...")
            
            # Initialize model architecture
            self.model = ChestXRayDetector(
                num_classes=len(self.finding_types),
                confidence_threshold=self.confidence_threshold
            )
            logger.debug(f"Initialized detection model architecture with {len(self.finding_types)} finding types")
            
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
                logger.info(f"Loading detection model weights from: {detection_model_path}")
                self.model.load_weights(detection_model_path)
                self.use_mock_detections = False
                logger.info(f"✓ Detection model loaded successfully from {detection_model_path}")
            else:
                logger.warning(f"Detection model not found at {detection_model_path}")
                logger.warning("Using mock detections for demonstration purposes")
                logger.warning("Train and save a detection model to enable real detections")
                self.use_mock_detections = True
            
            # Move model to device and set to evaluation mode
            self.model.to(self.device)
            self.model.eval()
            self.model_loaded = True
            logger.info(f"Detection model ready for inference on {self.device}")
            
        except Exception as e:
            logger.error(f"Error loading detection model: {str(e)}", exc_info=True)
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
            logger.warning("Detection model not loaded, attempting to load...")
            self.load_model()
        
        if self.model is None:
            logger.error("Detection model failed to load")
            raise RuntimeError("Detection model failed to load")
        
        logger.debug(f"Starting detection for image: {image_path}")
        start_time = time.time()
        
        # Preprocess image
        logger.debug("Preprocessing image for detection...")
        image_tensor = self.processor.process_image(image_path)
        image_tensor = image_tensor.to(self.device)
        
        # Run detection
        logger.debug(f"Running detection inference (mock={self.use_mock_detections})...")
        detections = self.model.detect(
            image_tensor, 
            return_mock=self.use_mock_detections
        )
        
        processing_time = time.time() - start_time
        
        logger.debug(f"Detection completed: Found {len(detections)} findings in {processing_time:.3f}s")
        
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
            logger.warning("Detection model not loaded, attempting to load...")
            self.load_model()
        
        if self.model is None:
            logger.error("Detection model failed to load")
            raise RuntimeError("Detection model failed to load")
        
        logger.info(f"Starting batch detection for {len(image_paths)} images")
        start_time = time.time()
        batch_detections = []
        
        for idx, image_path in enumerate(image_paths):
            try:
                logger.debug(f"Processing batch image {idx + 1}/{len(image_paths)}")
                detections, _ = self.detect(image_path)
                batch_detections.append(detections)
            except Exception as e:
                logger.error(f"Error processing {image_path}: {str(e)}")
                batch_detections.append([])
        
        total_processing_time = time.time() - start_time
        logger.info(f"Batch detection completed in {total_processing_time:.3f}s")
        
        return batch_detections, total_processing_time
    
    def set_confidence_threshold(self, threshold: float) -> None:
        """
        Update the confidence threshold for detections.
        
        Args:
            threshold: New confidence threshold (0.0 to 1.0)
        """
        if not 0.0 <= threshold <= 1.0:
            logger.error(f"Invalid confidence threshold: {threshold}")
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
        
        logger.info(f"Updating confidence threshold from {self.confidence_threshold} to {threshold}")
        self.confidence_threshold = threshold
        if self.model is not None:
            self.model.confidence_threshold = threshold
