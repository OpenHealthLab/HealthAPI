
from sqlalchemy.orm import Session
from app.models.database_models import Prediction
from app.schemas.prediction import PredictionCreate
import json

class PredictionService:
    @staticmethod
    def create_prediction(db: Session, prediction_data: PredictionCreate) -> Prediction:
        """Create a new prediction record in database"""
        db_prediction = Prediction(**prediction_data.model_dump())
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        return db_prediction
    
    @staticmethod
    def get_prediction(db: Session, prediction_id: int) -> Prediction:
        """Get a prediction by ID"""
        return db.query(Prediction).filter(Prediction.id == prediction_id).first()
    
    @staticmethod
    def get_predictions(db: Session, skip: int = 0, limit: int = 100):
        """Get all predictions with pagination"""
        return db.query(Prediction).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_predictions_by_class(db: Session, pred_class: str):
        """Get predictions filtered by class"""
        return db.query(Prediction).filter(
            Prediction.prediction_class == pred_class
        ).all()

