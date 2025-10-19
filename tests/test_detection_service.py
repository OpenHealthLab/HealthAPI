"""
Comprehensive test cases for DetectionService.

Tests cover detection CRUD operations, batch creation,
filtering, and edge cases.
"""

import pytest
from sqlalchemy.orm import Session
from typing import List

from app.services.detection_service import DetectionService
from app.models.database_models import Detection, Prediction
from app.schemas.detection import DetectionCreate, DetectionResult


class TestDetectionService:
    """Test suite for DetectionService."""
    
    @pytest.fixture
    def detection_service(self):
        """Create DetectionService instance."""
        return DetectionService()
    
    @pytest.fixture
    def test_prediction(self, db: Session):
        """Create a test prediction."""
        prediction = Prediction(
            image_filename="test_xray.png",
            prediction_class="PNEUMONIA",
            confidence_score=0.95,
            model_name="v1.0"
        )
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        return prediction
    
    @pytest.fixture
    def test_detection(self, db: Session, test_prediction):
        """Create a test detection."""
        detection = Detection(
            prediction_id=test_prediction.id,
            finding_type="Infiltrate",
            confidence_score=0.88,
            bbox_x1=0.1,
            bbox_y1=0.15,
            bbox_x2=0.3,
            bbox_y2=0.35
        )
        db.add(detection)
        db.commit()
        db.refresh(detection)
        return detection


class TestCreateDetection(TestDetectionService):
    """Tests for create_detection method."""
    
    def test_create_detection_success(self, db: Session, detection_service: DetectionService, test_prediction):
        """Test successful detection creation."""
        detection_data = DetectionCreate(
            prediction_id=test_prediction.id,
            finding_type="Nodule",
            confidence_score=0.92,
            bbox_x1=0.05,
            bbox_y1=0.075,
            bbox_x2=0.15,
            bbox_y2=0.175
        )
        
        detection = detection_service.create_detection(db, detection_data)
        
        assert detection.id is not None
        assert detection.prediction_id == test_prediction.id
        assert detection.finding_type == "Nodule"
        assert detection.confidence_score == 0.92
        assert detection.bbox_x1 == 50
        assert detection.bbox_y1 == 75
        assert detection.bbox_x2 == 150
        assert detection.bbox_y2 == 175
    
    def test_create_detection_invalid_prediction_id(self, db: Session, detection_service: DetectionService):
        """Test creating detection with non-existent prediction ID fails."""
        detection_data = DetectionCreate(
            prediction_id=99999,
            finding_type="Nodule",
            confidence_score=0.92,
            bbox_x1=0.05,
            bbox_y1=0.075,
            bbox_x2=0.15,
            bbox_y2=0.175
        )
        
        with pytest.raises(ValueError) as exc_info:
            detection_service.create_detection(db, detection_data)
        
        assert "not found" in str(exc_info.value)
    
    def test_create_detection_with_zero_confidence(self, db: Session, detection_service: DetectionService, test_prediction):
        """Test creating detection with zero confidence."""
        detection_data = DetectionCreate(
            prediction_id=test_prediction.id,
            finding_type="Uncertain",
            confidence_score=0.0,
            bbox_x1=0.01,
            bbox_y1=0.02,
            bbox_x2=0.03,
            bbox_y2=0.04
        )
        
        detection = detection_service.create_detection(db, detection_data)
        
        assert detection.confidence_score == 0.0
    
    def test_create_detection_with_max_confidence(self, db: Session, detection_service: DetectionService, test_prediction):
        """Test creating detection with maximum confidence."""
        detection_data = DetectionCreate(
            prediction_id=test_prediction.id,
            finding_type="Definite",
            confidence_score=1.0,
            bbox_x1=0.01,
            bbox_y1=0.02,
            bbox_x2=0.03,
            bbox_y2=0.04
        )
        
        detection = detection_service.create_detection(db, detection_data)
        
        assert detection.confidence_score == 1.0


class TestCreateDetectionsBatch(TestDetectionService):
    """Tests for create_detections_batch method."""
    
    def test_create_detections_batch_success(self, db: Session, detection_service: DetectionService, test_prediction):
        """Test successful batch detection creation."""
        detections_data = [
            DetectionCreate(
                prediction_id=test_prediction.id,
                finding_type="Nodule",
                confidence_score=0.90,
                bbox_x1=0.01,
                bbox_y1=0.02,
                bbox_x2=0.05,
                bbox_y2=0.06
            ),
            DetectionCreate(
                prediction_id=test_prediction.id,
                finding_type="Infiltrate",
                confidence_score=0.85,
                bbox_x1=0.1,
                bbox_y1=0.12,
                bbox_x2=0.2,
                bbox_y2=0.22
            ),
            DetectionCreate(
                prediction_id=test_prediction.id,
                finding_type="Effusion",
                confidence_score=0.78,
                bbox_x1=0.3,
                bbox_y1=0.35,
                bbox_x2=0.4,
                bbox_y2=0.45
            )
        ]
        
        detections = detection_service.create_detections_batch(db, detections_data)
        
        assert len(detections) == 3
        assert all(d.id is not None for d in detections)
        assert all(d.prediction_id == test_prediction.id for d in detections)
        assert detections[0].finding_type == "Nodule"
        assert detections[1].finding_type == "Infiltrate"
        assert detections[2].finding_type == "Effusion"
    
    def test_create_detections_batch_empty_list(self, db: Session, detection_service: DetectionService):
        """Test creating batch with empty list."""
        detections = detection_service.create_detections_batch(db, [])
        
        assert len(detections) == 0
    
    def test_create_detections_batch_single_item(self, db: Session, detection_service: DetectionService, test_prediction):
        """Test creating batch with single item."""
        detections_data = [
            DetectionCreate(
                prediction_id=test_prediction.id,
                finding_type="Nodule",
                confidence_score=0.90,
                bbox_x1=0.01,
                bbox_y1=0.02,
                bbox_x2=0.05,
                bbox_y2=0.06
            )
        ]
        
        detections = detection_service.create_detections_batch(db, detections_data)
        
        assert len(detections) == 1
    
    def test_create_detections_batch_invalid_prediction_id(self, db: Session, detection_service: DetectionService):
        """Test batch creation with invalid prediction ID fails."""
        detections_data = [
            DetectionCreate(
                prediction_id=99999,
                finding_type="Nodule",
                confidence_score=0.90,
                bbox_x1=0.01,
                bbox_y1=0.02,
                bbox_x2=0.05,
                bbox_y2=0.06
            )
        ]
        
        with pytest.raises(ValueError) as exc_info:
            detection_service.create_detections_batch(db, detections_data)
        
        assert "not found" in str(exc_info.value)
    
    def test_create_detections_batch_multiple_predictions(self, db: Session, detection_service: DetectionService):
        """Test batch creation with multiple predictions."""
        # Create two predictions
        pred1 = Prediction(
            image_filename="xray1.png",
            prediction_class="PNEUMONIA",
            confidence_score=0.95,
            model_name="v1.0"
        )
        pred2 = Prediction(
            image_filename="xray2.png",
            prediction_class="NORMAL",
            confidence_score=0.88,
            model_name="v1.0"
        )
        db.add_all([pred1, pred2])
        db.commit()
        
        detections_data = [
            DetectionCreate(
                prediction_id=pred1.id,
                finding_type="Nodule",
                confidence_score=0.90,
                bbox_x1=0.01,
                bbox_y1=0.02,
                bbox_x2=0.05,
                bbox_y2=0.06
            ),
            DetectionCreate(
                prediction_id=pred2.id,
                finding_type="Calcification",
                confidence_score=0.75,
                bbox_x1=0.1,
                bbox_y1=0.12,
                bbox_x2=0.15,
                bbox_y2=0.17
            )
        ]
        
        detections = detection_service.create_detections_batch(db, detections_data)
        
        assert len(detections) == 2
        assert detections[0].prediction_id == pred1.id
        assert detections[1].prediction_id == pred2.id


class TestGetDetectionsByPrediction(TestDetectionService):
    """Tests for get_detections_by_prediction method."""
    
    def test_get_detections_by_prediction_success(self, db: Session, detection_service: DetectionService, test_prediction, test_detection):
        """Test retrieving detections for a prediction."""
        detections = detection_service.get_detections_by_prediction(db, test_prediction.id)
        
        assert len(detections) == 1
        assert detections[0].id == test_detection.id
        assert detections[0].prediction_id == test_prediction.id
    
    def test_get_detections_by_prediction_multiple(self, db: Session, detection_service: DetectionService, test_prediction):
        """Test retrieving multiple detections for a prediction."""
        # Create multiple detections
        for i in range(3):
            detection = Detection(
                prediction_id=test_prediction.id,
                finding_type=f"Finding_{i}",
                confidence_score=0.8 + i * 0.05,
                bbox_x1=i * 10,
                bbox_y1=i * 20,
                bbox_x2=i * 10 + 50,
                bbox_y2=i * 20 + 50
            )
            db.add(detection)
        db.commit()
        
        detections = detection_service.get_detections_by_prediction(db, test_prediction.id)
        
        assert len(detections) == 3
        assert all(d.prediction_id == test_prediction.id for d in detections)
    
    def test_get_detections_by_prediction_none_found(self, db: Session, detection_service: DetectionService, test_prediction):
        """Test retrieving detections when none exist."""
        # Create a new prediction with no detections
        new_pred = Prediction(
            image_filename="empty.png",
            prediction_class="NORMAL",
            confidence_score=0.99,
            model_name="v1.0"
        )
        db.add(new_pred)
        db.commit()
        
        detections = detection_service.get_detections_by_prediction(db, new_pred.id)
        
        assert len(detections) == 0
    
    def test_get_detections_by_prediction_invalid_id(self, db: Session, detection_service: DetectionService):
        """Test retrieving detections for non-existent prediction."""
        detections = detection_service.get_detections_by_prediction(db, 99999)
        
        assert len(detections) == 0


class TestGetDetectionById(TestDetectionService):
    """Tests for get_detection_by_id method."""
    
    def test_get_detection_by_id_success(self, db: Session, detection_service: DetectionService, test_detection):
        """Test successful detection retrieval by ID."""
        detection = detection_service.get_detection_by_id(db, test_detection.id)
        
        assert detection is not None
        assert detection.id == test_detection.id
        assert detection.finding_type == test_detection.finding_type
    
    def test_get_detection_by_id_not_found(self, db: Session, detection_service: DetectionService):
        """Test retrieving non-existent detection."""
        detection = detection_service.get_detection_by_id(db, 99999)
        
        assert detection is None


class TestGetAllDetections(TestDetectionService):
    """Tests for get_all_detections method."""
    
    def test_get_all_detections_success(self, db: Session, detection_service: DetectionService, test_detection):
        """Test retrieving all detections."""
        detections = detection_service.get_all_detections(db)
        
        assert len(detections) >= 1
        assert any(d.id == test_detection.id for d in detections)
    
    def test_get_all_detections_pagination(self, db: Session, detection_service: DetectionService, test_prediction):
        """Test pagination of all detections."""
        # Create multiple detections
        for i in range(10):
            detection = Detection(
                prediction_id=test_prediction.id,
                finding_type=f"Finding_{i}",
                confidence_score=0.8,
                bbox_x1=i * 10,
                bbox_y1=i * 20,
                bbox_x2=i * 10 + 50,
                bbox_y2=i * 20 + 50
            )
            db.add(detection)
        db.commit()
        
        # Get first page
        page1 = detection_service.get_all_detections(db, skip=0, limit=5)
        assert len(page1) == 5
        
        # Get second page
        page2 = detection_service.get_all_detections(db, skip=5, limit=5)
        assert len(page2) == 5
        
        # Verify no overlap
        page1_ids = {d.id for d in page1}
        page2_ids = {d.id for d in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0
    
    def test_get_all_detections_custom_limit(self, db: Session, detection_service: DetectionService, test_prediction):
        """Test custom limit for all detections."""
        # Create multiple detections
        for i in range(5):
            detection = Detection(
                prediction_id=test_prediction.id,
                finding_type=f"Finding_{i}",
                confidence_score=0.8,
                bbox_x1=i * 10,
                bbox_y1=i * 20,
                bbox_x2=i * 10 + 50,
                bbox_y2=i * 20 + 50
            )
            db.add(detection)
        db.commit()
        
        detections = detection_service.get_all_detections(db, limit=3)
        
        assert len(detections) <= 3


class TestGetDetectionsByFindingType(TestDetectionService):
    """Tests for get_detections_by_finding_type method."""
    
    def test_get_detections_by_finding_type_success(self, db: Session, detection_service: DetectionService, test_prediction):
        """Test filtering detections by finding type."""
        # Create detections with different types
        types = ["Nodule", "Infiltrate", "Nodule", "Effusion", "Nodule"]
        for finding_type in types:
            detection = Detection(
                prediction_id=test_prediction.id,
                finding_type=finding_type,
                confidence_score=0.8,
                bbox_x1=0.01,
                bbox_y1=0.02,
                bbox_x2=0.05,
                bbox_y2=0.06
            )
            db.add(detection)
        db.commit()
        
        nodule_detections = detection_service.get_detections_by_finding_type(db, "Nodule")
        
        assert len(nodule_detections) == 3
        assert all(d.finding_type == "Nodule" for d in nodule_detections)
    
    def test_get_detections_by_finding_type_none_found(self, db: Session, detection_service: DetectionService, test_detection):
        """Test filtering by non-existent finding type."""
        detections = detection_service.get_detections_by_finding_type(db, "NonExistent")
        
        assert len(detections) == 0
    
    def test_get_detections_by_finding_type_pagination(self, db: Session, detection_service: DetectionService, test_prediction):
        """Test pagination with finding type filter."""
        # Create multiple detections of same type
        for i in range(10):
            detection = Detection(
                prediction_id=test_prediction.id,
                finding_type="Nodule",
                confidence_score=0.8,
                bbox_x1=i * 10,
                bbox_y1=i * 20,
                bbox_x2=i * 10 + 50,
                bbox_y2=i * 20 + 50
            )
            db.add(detection)
        db.commit()
        
        page1 = detection_service.get_detections_by_finding_type(db, "Nodule", skip=0, limit=5)
        page2 = detection_service.get_detections_by_finding_type(db, "Nodule", skip=5, limit=5)
        
        assert len(page1) == 5
        assert len(page2) == 5
        assert all(d.finding_type == "Nodule" for d in page1 + page2)


class TestDeleteDetection(TestDetectionService):
    """Tests for delete_detection method."""
    
    def test_delete_detection_success(self, db: Session, detection_service: DetectionService, test_detection):
        """Test successful detection deletion."""
        detection_id = test_detection.id
        
        result = detection_service.delete_detection(db, detection_id)
        
        assert result is True
        
        # Verify deletion
        deleted = db.query(Detection).filter(Detection.id == detection_id).first()
        assert deleted is None
    
    def test_delete_detection_not_found(self, db: Session, detection_service: DetectionService):
        """Test deleting non-existent detection."""
        result = detection_service.delete_detection(db, 99999)
        
        assert result is False
    
    def test_delete_detection_does_not_affect_prediction(self, db: Session, detection_service: DetectionService, test_detection, test_prediction):
        """Test that deleting detection doesn't delete prediction."""
        detection_service.delete_detection(db, test_detection.id)
        
        # Verify prediction still exists
        prediction = db.query(Prediction).filter(Prediction.id == test_prediction.id).first()
        assert prediction is not None


class TestEdgeCases(TestDetectionService):
    """Tests for edge cases and special scenarios."""
    
    def test_detection_with_overlapping_bboxes(self, db: Session, detection_service: DetectionService, test_prediction):
        """Test creating detections with overlapping bounding boxes."""
        detections_data = [
            DetectionCreate(
                prediction_id=test_prediction.id,
                finding_type="Nodule",
                confidence_score=0.90,
                bbox_x1=0.1,
                bbox_y1=0.1,
                bbox_x2=0.2,
                bbox_y2=0.2
            ),
            DetectionCreate(
                prediction_id=test_prediction.id,
                finding_type="Infiltrate",
                confidence_score=0.85,
                bbox_x1=0.15,
                bbox_y1=0.15,
                bbox_x2=0.25,
                bbox_y2=0.25
            )
        ]
        
        detections = detection_service.create_detections_batch(db, detections_data)
        
        assert len(detections) == 2
    
    def test_detection_with_same_coordinates(self, db: Session, detection_service: DetectionService, test_prediction):
        """Test creating detection where bbox coordinates are equal."""
        detection_data = DetectionCreate(
            prediction_id=test_prediction.id,
            finding_type="Point",
            confidence_score=0.90,
            bbox_x1=0.1,
            bbox_y1=0.1,
            bbox_x2=0.1,
            bbox_y2=0.1
        )
        
        detection = detection_service.create_detection(db, detection_data)
        
        assert detection.bbox_x1 == detection.bbox_x2
        assert detection.bbox_y1 == detection.bbox_y2
    
    def test_detection_with_negative_coordinates(self, db: Session, detection_service: DetectionService, test_prediction):
        """Test creating detection with negative coordinates."""
        detection_data = DetectionCreate(
            prediction_id=test_prediction.id,
            finding_type="Edge",
            confidence_score=0.80,
            bbox_x1=-0.01,
            bbox_y1=-0.02,
            bbox_x2=0.05,
            bbox_y2=0.06
        )
        
        detection = detection_service.create_detection(db, detection_data)
        
        assert detection.bbox_x1 == -10
        assert detection.bbox_y1 == -20
    
    def test_multiple_detections_same_type_same_prediction(self, db: Session, detection_service: DetectionService, test_prediction):
        """Test creating multiple detections of same type for one prediction."""
        detections_data = [
            DetectionCreate(
                prediction_id=test_prediction.id,
                finding_type="Nodule",
                confidence_score=0.90,
                bbox_x1=i * 100,
                bbox_y1=i * 100,
                bbox_x2=i * 100 + 50,
                bbox_y2=i * 100 + 50
            )
            for i in range(5)
        ]
        
        detections = detection_service.create_detections_batch(db, detections_data)
        
        assert len(detections) == 5
        assert all(d.finding_type == "Nodule" for d in detections)
        assert all(d.prediction_id == test_prediction.id for d in detections)
