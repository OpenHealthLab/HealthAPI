"""
Pydantic schemas for CADe (Computer-Aided Detection) endpoints.

These schemas define the structure for detection results including
bounding boxes and finding classifications.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional


class BoundingBox(BaseModel):
    """
    Schema for bounding box coordinates.
    
    Coordinates are normalized to 0-1 range relative to image dimensions.
    
    Attributes:
        x1: Top-left x coordinate (0.0 to 1.0)
        y1: Top-left y coordinate (0.0 to 1.0)
        x2: Bottom-right x coordinate (0.0 to 1.0)
        y2: Bottom-right y coordinate (0.0 to 1.0)
    """
    
    x1: float = Field(ge=0.0, le=1.0, description="Top-left x coordinate")
    y1: float = Field(ge=0.0, le=1.0, description="Top-left y coordinate")
    x2: float = Field(ge=0.0, le=1.0, description="Bottom-right x coordinate")
    y2: float = Field(ge=0.0, le=1.0, description="Bottom-right y coordinate")


class DetectionResult(BaseModel):
    """
    Schema for a single detection result.
    
    Represents one finding detected by the CADe model.
    
    Attributes:
        id: Unique identifier for the detection
        prediction_id: Associated prediction ID
        finding_type: Type of finding detected
        confidence_score: Detection confidence (0.0 to 1.0)
        bounding_box: Bounding box coordinates
        created_at: When the detection was created
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    prediction_id: int
    finding_type: str
    confidence_score: float
    bounding_box: BoundingBox
    created_at: datetime
    
    @classmethod
    def from_db_model(cls, db_detection):
        """Create DetectionResult from database Detection model"""
        # Normalize coordinates from pixel values to 0-1 range
        # Database stores pixel values (multiplied by 1000), so divide to get normalized coords
        x1 = db_detection.bbox_x1 / 1000.0 if db_detection.bbox_x1 > 1.0 else db_detection.bbox_x1
        y1 = db_detection.bbox_y1 / 1000.0 if db_detection.bbox_y1 > 1.0 else db_detection.bbox_y1
        x2 = db_detection.bbox_x2 / 1000.0 if db_detection.bbox_x2 > 1.0 else db_detection.bbox_x2
        y2 = db_detection.bbox_y2 / 1000.0 if db_detection.bbox_y2 > 1.0 else db_detection.bbox_y2
        
        return cls(
            id=db_detection.id,
            prediction_id=db_detection.prediction_id,
            finding_type=db_detection.finding_type,
            confidence_score=db_detection.confidence_score,
            bounding_box=BoundingBox(
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2
            ),
            created_at=db_detection.created_at
        )


class DetectionCreate(BaseModel):
    """
    Schema for creating a new detection record.
    
    Used internally to validate data before inserting into database.
    
    Attributes:
        prediction_id: Associated prediction ID
        finding_type: Type of finding detected
        confidence_score: Detection confidence
        bbox_x1: Top-left x coordinate (normalized 0-1 or pixel values)
        bbox_y1: Top-left y coordinate (normalized 0-1 or pixel values)
        bbox_x2: Bottom-right x coordinate (normalized 0-1 or pixel values)
        bbox_y2: Bottom-right y coordinate (normalized 0-1 or pixel values)
    """
    
    prediction_id: int
    finding_type: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    bbox_x1: float
    bbox_y1: float
    bbox_x2: float
    bbox_y2: float


class CADeResponse(BaseModel):
    """
    Schema for CADe detection response.
    
    Contains all detections for a single image.
    
    Attributes:
        prediction_id: Associated prediction ID
        image_filename: Name of the analyzed image
        model_name: Name/version of the detection model
        num_findings: Number of findings detected
        processing_time: Time taken for detection
        detections: List of individual detections
    """
    
    prediction_id: int
    image_filename: str
    model_name: str
    num_findings: int
    processing_time: float
    detections: List[DetectionResult]


class BatchCADeResponse(BaseModel):
    """
    Schema for batch CADe detection response.
    
    Returns summary statistics and individual detection results for a batch.
    
    Attributes:
        total_images: Total number of images processed
        successful: Number of successful detections
        failed: Number of failed detections
        total_processing_time: Total time taken for all detections
        results: List of CADe responses for each image
        errors: List of errors for failed detections
    """
    
    total_images: int
    successful: int
    failed: int
    total_processing_time: float
    results: List[CADeResponse]
    errors: List[dict] = []
