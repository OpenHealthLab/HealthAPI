
from sqlalchemy.orm import Session
from app.models.database_models import Prediction
from app.schemas.prediction import PredictionCreate
from typing import List
import json


class PredictionService:
    """
    Service class for prediction-related operations.
    
    This service encapsulates business logic for managing prediction records
    in the database. Uses dependency injection for better testability and
    separation of concerns.
    """
    
    def create_prediction(self, db: Session, prediction_data: PredictionCreate) -> Prediction:
        """Create a new prediction record in database"""
        db_prediction = Prediction(**prediction_data.model_dump())
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        return db_prediction
    
    def create_predictions_batch(self, db: Session, predictions_data: List[PredictionCreate]) -> List[Prediction]:
        """Create multiple prediction records in database as a batch"""
        db_predictions = []
        for prediction_data in predictions_data:
            db_prediction = Prediction(**prediction_data.model_dump())
            db_predictions.append(db_prediction)
        
        db.add_all(db_predictions)
        db.commit()
        
        for db_prediction in db_predictions:
            db.refresh(db_prediction)
        
        return db_predictions
    
    def get_prediction(self, db: Session, prediction_id: int) -> Prediction:
        """Get a prediction by ID"""
        return db.query(Prediction).filter(Prediction.id == prediction_id).first()
    
    def get_predictions(self, db: Session, skip: int = 0, limit: int = 100):
        """Get all predictions with pagination"""
        return db.query(Prediction).offset(skip).limit(limit).all()
    
    def get_predictions_by_class(self, db: Session, pred_class: str):
        """Get predictions filtered by class"""
        return db.query(Prediction).filter(
            Prediction.prediction_class == pred_class
        ).all()
