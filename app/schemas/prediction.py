from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict

class PredictionResponse(BaseModel):
    id: int
    image_filename: str
    model_name: str
    prediction_class: str
    confidence_score: float
    processing_time: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True

class PredictionCreate(BaseModel):
    image_filename: str
    model_name: str = "chest_xray_v1"
    prediction_class: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    processing_time: Optional[float] = None
    metadata: Optional[str] = None

