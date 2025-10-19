"""
Detection service for CADe business logic.

This module handles the business logic for creating and retrieving
detection records from the database.
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.database_models import Detection, Prediction
from app.schemas.detection import DetectionCreate, DetectionResult


class DetectionService:
    """
    Service class for detection-related database operations.
    
    Provides methods to create and retrieve detection records,
    encapsulating database interaction logic. Uses dependency injection
    for better testability and separation of concerns.
    """
    
    def create_detection(self, db: Session, detection_data: DetectionCreate) -> Detection:
        """
        Create a single detection record in the database.
        
        Args:
            db: Database session
            detection_data: Detection data to create
            
        Returns:
            Created Detection database object
            
        Raises:
            ValueError: If prediction_id doesn't exist
        """
        # Verify prediction exists
        prediction = db.query(Prediction).filter(
            Prediction.id == detection_data.prediction_id
        ).first()
        
        if not prediction:
            raise ValueError(f"Prediction with id {detection_data.prediction_id} not found")
        
        # Convert normalized coordinates (0-1) to pixel values (multiply by 1000)
        bbox_x1 = detection_data.bbox_x1 * 1000 if detection_data.bbox_x1 <= 1.0 else detection_data.bbox_x1
        bbox_y1 = detection_data.bbox_y1 * 1000 if detection_data.bbox_y1 <= 1.0 else detection_data.bbox_y1
        bbox_x2 = detection_data.bbox_x2 * 1000 if detection_data.bbox_x2 <= 1.0 else detection_data.bbox_x2
        bbox_y2 = detection_data.bbox_y2 * 1000 if detection_data.bbox_y2 <= 1.0 else detection_data.bbox_y2
        
        # Create detection record
        db_detection = Detection(
            prediction_id=detection_data.prediction_id,
            finding_type=detection_data.finding_type,
            confidence_score=detection_data.confidence_score,
            bbox_x1=bbox_x1,
            bbox_y1=bbox_y1,
            bbox_x2=bbox_x2,
            bbox_y2=bbox_y2
        )
        
        db.add(db_detection)
        db.commit()
        db.refresh(db_detection)
        
        return db_detection
    
    def create_detections_batch(
        self,
        db: Session, 
        detections_data: List[DetectionCreate]
    ) -> List[Detection]:
        """
        Create multiple detection records in a single transaction.
        
        Args:
            db: Database session
            detections_data: List of detection data to create
            
        Returns:
            List of created Detection database objects
            
        Raises:
            ValueError: If any prediction_id doesn't exist
        """
        db_detections = []
        
        for detection_data in detections_data:
            # Verify prediction exists
            prediction = db.query(Prediction).filter(
                Prediction.id == detection_data.prediction_id
            ).first()
            
            if not prediction:
                raise ValueError(f"Prediction with id {detection_data.prediction_id} not found")
            
            # Convert normalized coordinates (0-1) to pixel values (multiply by 1000)
            bbox_x1 = detection_data.bbox_x1 * 1000 if detection_data.bbox_x1 <= 1.0 else detection_data.bbox_x1
            bbox_y1 = detection_data.bbox_y1 * 1000 if detection_data.bbox_y1 <= 1.0 else detection_data.bbox_y1
            bbox_x2 = detection_data.bbox_x2 * 1000 if detection_data.bbox_x2 <= 1.0 else detection_data.bbox_x2
            bbox_y2 = detection_data.bbox_y2 * 1000 if detection_data.bbox_y2 <= 1.0 else detection_data.bbox_y2
            
            # Create detection record
            db_detection = Detection(
                prediction_id=detection_data.prediction_id,
                finding_type=detection_data.finding_type,
                confidence_score=detection_data.confidence_score,
                bbox_x1=bbox_x1,
                bbox_y1=bbox_y1,
                bbox_x2=bbox_x2,
                bbox_y2=bbox_y2
            )
            
            db_detections.append(db_detection)
        
        # Add all detections in batch
        db.add_all(db_detections)
        db.commit()
        
        # Refresh all objects
        for db_detection in db_detections:
            db.refresh(db_detection)
        
        return db_detections
    
    def get_detections_by_prediction(
        self,
        db: Session,
        prediction_id: int
    ) -> List[Detection]:
        """
        Get all detections for a specific prediction.
        
        Args:
            db: Database session
            prediction_id: ID of the prediction
            
        Returns:
            List of Detection objects
        """
        detections = db.query(Detection).filter(
            Detection.prediction_id == prediction_id
        ).all()
        
        return detections
    
    def get_detection_by_id(
        self,
        db: Session,
        detection_id: int
    ) -> Optional[Detection]:
        """
        Get a specific detection by ID.
        
        Args:
            db: Database session
            detection_id: ID of the detection
            
        Returns:
            Detection object or None if not found
        """
        detection = db.query(Detection).filter(
            Detection.id == detection_id
        ).first()
        
        return detection
    
    def get_all_detections(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Detection]:
        """
        Get all detections with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Detection objects
        """
        detections = db.query(Detection).offset(skip).limit(limit).all()
        
        return detections
    
    def get_detections_by_finding_type(
        self,
        db: Session,
        finding_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Detection]:
        """
        Get detections filtered by finding type.
        
        Args:
            db: Database session
            finding_type: Type of finding to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Detection objects
        """
        detections = db.query(Detection).filter(
            Detection.finding_type == finding_type
        ).offset(skip).limit(limit).all()
        
        return detections
    
    def delete_detection(self, db: Session, detection_id: int) -> bool:
        """
        Delete a detection record.
        
        Args:
            db: Database session
            detection_id: ID of the detection to delete
            
        Returns:
            True if deleted, False if not found
        """
        detection = db.query(Detection).filter(
            Detection.id == detection_id
        ).first()
        
        if detection:
            db.delete(detection)
            db.commit()
            return True
        
        return False
