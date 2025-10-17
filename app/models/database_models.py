"""
Database models for the application.

This module defines SQLAlchemy ORM models that represent
database tables and their relationships.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Prediction(Base):
    """
    Model for storing chest X-ray prediction results.
    
    This table stores all predictions made by the ML model,
    including metadata about the prediction process and DICOM metadata.
    
    Attributes:
        id: Primary key, auto-incrementing
        image_filename: Name of the uploaded image file
        model_name: Name/version of the model used
        prediction_class: Predicted class (Normal, Pneumonia, COVID-19)
        confidence_score: Model confidence (0.0 to 1.0)
        processing_time: Time taken for inference in seconds
        prediction_metadata: Additional metadata as JSON string
        dicom_metadata: DICOM metadata as JSON string (HIPAA-compliant, no PHI)
        created_at: Timestamp when prediction was created
        
    Example:
        >>> prediction = Prediction(
        >>>     image_filename="xray_001.png",
        >>>     model_name="chest_xray_v1",
        >>>     prediction_class="Normal",
        >>>     confidence_score=0.95
        >>> )
        >>> db.add(prediction)
        >>> db.commit()
    """
    
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    image_filename = Column(String, nullable=False, index=True)
    model_name = Column(String, default="chest_xray_v1")
    prediction_class = Column(String, nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)
    processing_time = Column(Float)
    prediction_metadata = Column(Text)  # Store additional data as JSON
    dicom_metadata = Column(Text)  # DICOM metadata as JSON (HIPAA-compliant)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self) -> str:
        """String representation of the Prediction object."""
        return (
            f"<Prediction(id={self.id}, "
            f"class={self.prediction_class}, "
            f"confidence={self.confidence_score:.2f})>"
        )


class Detection(Base):
    """
    Model for storing CADe (Computer-Aided Detection) results.
    
    This table stores individual findings detected by the CADe model,
    with bounding box coordinates and finding classifications.
    
    Attributes:
        id: Primary key, auto-incrementing
        prediction_id: Foreign key to associated Prediction
        finding_type: Type of finding (Nodule, Pneumothorax, etc.)
        confidence_score: Detection confidence (0.0 to 1.0)
        bbox_x1: Bounding box top-left x coordinate (normalized 0-1)
        bbox_y1: Bounding box top-left y coordinate (normalized 0-1)
        bbox_x2: Bounding box bottom-right x coordinate (normalized 0-1)
        bbox_y2: Bounding box bottom-right y coordinate (normalized 0-1)
        created_at: Timestamp when detection was created
        
    Example:
        >>> detection = Detection(
        >>>     prediction_id=1,
        >>>     finding_type="Pulmonary Nodule",
        >>>     confidence_score=0.89,
        >>>     bbox_x1=0.3, bbox_y1=0.4,
        >>>     bbox_x2=0.5, bbox_y2=0.6
        >>> )
        >>> db.add(detection)
        >>> db.commit()
    """
    
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False, index=True)
    finding_type = Column(String, nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)
    bbox_x1 = Column(Float, nullable=False)  # Normalized coordinates (0-1)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationship
    prediction = relationship("Prediction", backref="detections")
    
    def __repr__(self) -> str:
        """String representation of the Detection object."""
        return (
            f"<Detection(id={self.id}, "
            f"finding={self.finding_type}, "
            f"confidence={self.confidence_score:.2f})>"
        )
