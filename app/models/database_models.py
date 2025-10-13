from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    image_filename = Column(String, nullable=False)
    model_name = Column(String, default="chest_xray_v1")
    prediction_class = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    processing_time = Column(Float)
    metadata = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Prediction(id={self.id}, class={self.prediction_class}, confidence={self.confidence_score})>"

