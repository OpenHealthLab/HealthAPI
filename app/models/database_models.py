"""
Database models for the application.

This module defines SQLAlchemy ORM models that represent
database tables and their relationships.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class Prediction(Base):
    """
    Model for storing chest X-ray prediction results.
    
    This table stores all predictions made by the ML model,
    including metadata about the prediction process.
    
    Attributes:
        id: Primary key, auto-incrementing
        image_filename: Name of the uploaded image file
        model_name: Name/version of the model used
        prediction_class: Predicted class (Normal, Pneumonia, COVID-19)
        confidence_score: Model confidence (0.0 to 1.0)
        processing_time: Time taken for inference in seconds
        prediction_metadata: Additional metadata as JSON string
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
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self) -> str:
        """String representation of the Prediction object."""
        return (
            f"<Prediction(id={self.id}, "
            f"class={self.prediction_class}, "
            f"confidence={self.confidence_score:.2f})>"
        )
