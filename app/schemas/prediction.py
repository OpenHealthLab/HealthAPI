"""
Pydantic schemas for request/response validation.

These schemas define the structure of data for API requests and responses,
providing automatic validation and serialization.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, List


class HealthCheck(BaseModel):
    """
    Schema for health check endpoint response.
    
    Attributes:
        status: Current status of the application
        app_name: Name of the application
        version: Application version
        model_loaded: Whether the ML model is loaded
    """
    
    status: str
    app_name: str
    version: str
    model_loaded: bool


class PredictionResponse(BaseModel):
    """
    Schema for prediction response.
    
    This is returned when a prediction is successfully created
    or when retrieving existing predictions.
    
    Attributes:
        id: Unique identifier for the prediction
        image_filename: Name of the uploaded image
        model_name: Name/version of the model used
        prediction_class: Predicted class
        confidence_score: Model confidence (0.0 to 1.0)
        processing_time: Time taken for inference
        created_at: When the prediction was created
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    image_filename: str
    model_name: str
    prediction_class: str
    confidence_score: float
    processing_time: Optional[float] = None
    created_at: datetime


class PredictionCreate(BaseModel):
    """
    Schema for creating a new prediction record.
    
    Used internally to validate data before inserting into database.
    
    Attributes:
        image_filename: Name of the uploaded image
        model_name: Name/version of the model used
        prediction_class: Predicted class
        confidence_score: Model confidence (must be between 0.0 and 1.0)
        processing_time: Time taken for inference
        prediction_metadata: Additional metadata as JSON string
    """
    
    image_filename: str
    model_name: str = "chest_xray_v1"
    prediction_class: str
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    processing_time: Optional[float] = None
    prediction_metadata: Optional[str] = None


class BatchPredictionResponse(BaseModel):
    """
    Schema for batch prediction response.
    
    Returns summary statistics and individual predictions for a batch.
    
    Attributes:
        total_images: Total number of images processed
        successful: Number of successful predictions
        failed: Number of failed predictions
        total_processing_time: Total time taken for all predictions
        predictions: List of individual prediction results
        errors: List of errors for failed predictions
    """
    
    total_images: int
    successful: int
    failed: int
    total_processing_time: float
    predictions: List[PredictionResponse]
    errors: List[Dict[str, str]] = []
