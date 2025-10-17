
from PIL import Image
import torch
from torchvision import transforms
import numpy as np
import pydicom
from typing import Tuple, Dict, Optional
import os

class ImageProcessor:
    """
    Image preprocessing for chest X-ray images.
    
    Supports both standard image formats (PNG, JPEG) and DICOM files.
    Handles DICOM pixel data conversion and metadata extraction.
    """
    
    def __init__(self, img_size=224):
        self.img_size = img_size
        self.transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.Grayscale(num_output_channels=1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485], std=[0.229])
        ])
    
    def is_dicom(self, image_path: str) -> bool:
        """Check if file is a DICOM file"""
        try:
            # Check by extension first
            if image_path.lower().endswith('.dcm'):
                return True
            # Try to read as DICOM
            pydicom.dcmread(image_path, stop_before_pixels=True)
            return True
        except:
            return False
    
    def process_dicom(self, image_path: str) -> Tuple[Image.Image, Dict]:
        """
        Process DICOM file and extract pixel data and metadata.
        
        Args:
            image_path: Path to DICOM file
            
        Returns:
            Tuple of (PIL Image, metadata dict)
            
        Note:
            Metadata excludes PHI per HIPAA best practices
        """
        try:
            # Read DICOM file
            ds = pydicom.dcmread(image_path)
            
            # Extract pixel data
            pixel_array = ds.pixel_array
            
            # Handle different photometric interpretations
            photometric = str(ds.get('PhotometricInterpretation', 'MONOCHROME2'))
            
            # MONOCHROME1: lower values = brighter (inverted)
            # MONOCHROME2: higher values = brighter (normal)
            if photometric == 'MONOCHROME1':
                pixel_array = np.max(pixel_array) - pixel_array
            
            # Normalize to 0-255 range
            pixel_array = pixel_array.astype(np.float32)
            pixel_min, pixel_max = pixel_array.min(), pixel_array.max()
            if pixel_max > pixel_min:
                pixel_array = ((pixel_array - pixel_min) / (pixel_max - pixel_min) * 255).astype(np.uint8)
            else:
                pixel_array = pixel_array.astype(np.uint8)
            
            # Convert to PIL Image
            image = Image.fromarray(pixel_array)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract HIPAA-compliant metadata (no PHI)
            metadata = {
                'modality': str(ds.get('Modality', 'Unknown')),
                'study_instance_uid': str(ds.get('StudyInstanceUID', '')),
                'series_instance_uid': str(ds.get('SeriesInstanceUID', '')),
                'study_date': str(ds.get('StudyDate', '')),
                'photometric_interpretation': photometric,
                'rows': int(ds.get('Rows', 0)),
                'columns': int(ds.get('Columns', 0)),
                'bits_stored': int(ds.get('BitsStored', 0)),
                'window_center': str(ds.get('WindowCenter', '')),
                'window_width': str(ds.get('WindowWidth', '')),
            }
            
            return image, metadata
            
        except Exception as e:
            raise ValueError(f"Error processing DICOM file: {str(e)}")
    
    def process_image(self, image_path: str) -> torch.Tensor:
        """
        Process image for model input.
        
        Supports both standard image formats and DICOM files.
        
        Args:
            image_path: Path to image or DICOM file
            
        Returns:
            Preprocessed image tensor ready for model inference
        """
        try:
            # Check if DICOM
            if self.is_dicom(image_path):
                image, _ = self.process_dicom(image_path)
            else:
                image = Image.open(image_path).convert('RGB')
            
            # Apply transforms
            tensor = self.transform(image)
            return tensor.unsqueeze(0)
            
        except Exception as e:
            raise ValueError(f"Error processing image: {str(e)}")
    
    def process_image_with_metadata(self, image_path: str) -> Tuple[torch.Tensor, Optional[Dict]]:
        """
        Process image and return both tensor and metadata.
        
        Args:
            image_path: Path to image or DICOM file
            
        Returns:
            Tuple of (image tensor, metadata dict or None)
        """
        try:
            metadata = None
            
            # Check if DICOM
            if self.is_dicom(image_path):
                image, metadata = self.process_dicom(image_path)
            else:
                image = Image.open(image_path).convert('RGB')
            
            # Apply transforms
            tensor = self.transform(image)
            return tensor.unsqueeze(0), metadata
            
        except Exception as e:
            raise ValueError(f"Error processing image: {str(e)}")
    
    def validate_image(self, image_path: str) -> bool:
        """
        Validate image format and size.
        
        Supports PNG, JPEG, and DICOM formats.
        """
        try:
            # Check if DICOM
            if self.is_dicom(image_path):
                ds = pydicom.dcmread(image_path, stop_before_pixels=True)
                # Validate it has pixel data attribute
                return hasattr(ds, 'PixelData') or 'PixelData' in ds
            else:
                # Standard image validation
                image = Image.open(image_path)
                if image.format not in ['PNG', 'JPEG', 'JPG']:
                    return False
                return True
        except:
            return False
