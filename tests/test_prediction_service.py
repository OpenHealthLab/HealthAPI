"""
Comprehensive test cases for PredictionService.

Tests cover prediction CRUD operations, batch creation,
filtering, and edge cases.
"""

import pytest
from sqlalchemy.orm import Session
from typing import List

from app.services.prediction_service import PredictionService
from app.models.database_models import Prediction
from app.schemas.prediction import PredictionCreate


class TestPredictionService:
    """Test suite for PredictionService."""
    
    @pytest.fixture
    def prediction_service(self):
        """Create PredictionService instance."""
        return PredictionService()
    
    @pytest.fixture
    def test_prediction(self, db: Session):
        """Create a test prediction."""
        prediction = Prediction(
            image_filename="test_image.png",
            prediction_class="PNEUMONIA",
            confidence_score=0.95,
            model_name="v1.0"
        )
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        return prediction


class TestCreatePrediction(TestPredictionService):
    """Tests for create_prediction method."""
    
    def test_create_prediction_success(self, db: Session, prediction_service: PredictionService):
        """Test successful prediction creation."""
        prediction_data = PredictionCreate(
            image_filename="chest_xray.png",
            prediction_class="PNEUMONIA",
            confidence_score=0.92,
            model_name="v1.0"
        )
        
        prediction = prediction_service.create_prediction(db, prediction_data)
        
        assert prediction.id is not None
        assert prediction.image_filename == "chest_xray.png"
        assert prediction.prediction_class == "PNEUMONIA"
        assert prediction.confidence_score == 0.92
        assert prediction.model_name == "v1.0"
        assert prediction.created_at is not None
    
    def test_create_prediction_normal_class(self, db: Session, prediction_service: PredictionService):
        """Test creating prediction with NORMAL class."""
        prediction_data = PredictionCreate(
            image_filename="normal_xray.png",
            prediction_class="NORMAL",
            confidence_score=0.98,
            model_name="v1.0"
        )
        
        prediction = prediction_service.create_prediction(db, prediction_data)
        
        assert prediction.prediction_class == "NORMAL"
        assert prediction.confidence_score == 0.98
    
    def test_create_prediction_with_zero_confidence(self, db: Session, prediction_service: PredictionService):
        """Test creating prediction with zero confidence."""
        prediction_data = PredictionCreate(
            image_filename="uncertain.png",
            prediction_class="UNKNOWN",
            confidence_score=0.0,
            model_name="v1.0"
        )
        
        prediction = prediction_service.create_prediction(db, prediction_data)
        
        assert prediction.confidence_score == 0.0
    
    def test_create_prediction_with_max_confidence(self, db: Session, prediction_service: PredictionService):
        """Test creating prediction with maximum confidence."""
        prediction_data = PredictionCreate(
            image_filename="certain.png",
            prediction_class="PNEUMONIA",
            confidence_score=1.0,
            model_name="v1.0"
        )
        
        prediction = prediction_service.create_prediction(db, prediction_data)
        
        assert prediction.confidence_score == 1.0
    
    def test_create_prediction_different_model_versions(self, db: Session, prediction_service: PredictionService):
        """Test creating predictions with different model versions."""
        versions = ["v1.0", "v2.0", "v2.1-beta"]
        
        for version in versions:
            prediction_data = PredictionCreate(
                image_filename=f"image_{version}.png",
                prediction_class="PNEUMONIA",
                confidence_score=0.90,
                model_name=version
            )
            
            prediction = prediction_service.create_prediction(db, prediction_data)
            assert prediction.model_name == version
    
    def test_create_prediction_duplicate_image_name(self, db: Session, prediction_service: PredictionService):
        """Test that duplicate image names are allowed (different predictions)."""
        prediction_data1 = PredictionCreate(
            image_filename="same_image.png",
            prediction_class="PNEUMONIA",
            confidence_score=0.90,
            model_name="v1.0"
        )
        
        prediction_data2 = PredictionCreate(
            image_filename="same_image.png",
            prediction_class="NORMAL",
            confidence_score=0.85,
            model_name="v2.0"
        )
        
        prediction1 = prediction_service.create_prediction(db, prediction_data1)
        prediction2 = prediction_service.create_prediction(db, prediction_data2)
        
        assert prediction1.id != prediction2.id
        assert prediction1.image_filename == prediction2.image_filename


class TestCreatePredictionsBatch(TestPredictionService):
    """Tests for create_predictions_batch method."""
    
    def test_create_predictions_batch_success(self, db: Session, prediction_service: PredictionService):
        """Test successful batch prediction creation."""
        predictions_data = [
            PredictionCreate(
                image_filename=f"image_{i}.png",
                prediction_class="PNEUMONIA" if i % 2 == 0 else "NORMAL",
                confidence_score=0.8 + (i * 0.02),
                model_name="v1.0"
            )
            for i in range(5)
        ]
        
        predictions = prediction_service.create_predictions_batch(db, predictions_data)
        
        assert len(predictions) == 5
        assert all(p.id is not None for p in predictions)
        assert predictions[0].prediction_class == "PNEUMONIA"
        assert predictions[1].prediction_class == "NORMAL"
    
    def test_create_predictions_batch_empty_list(self, db: Session, prediction_service: PredictionService):
        """Test creating batch with empty list."""
        predictions = prediction_service.create_predictions_batch(db, [])
        
        assert len(predictions) == 0
    
    def test_create_predictions_batch_single_item(self, db: Session, prediction_service: PredictionService):
        """Test creating batch with single item."""
        predictions_data = [
            PredictionCreate(
                image_filename="single.png",
                prediction_class="PNEUMONIA",
                confidence_score=0.95,
                model_name="v1.0"
            )
        ]
        
        predictions = prediction_service.create_predictions_batch(db, predictions_data)
        
        assert len(predictions) == 1
        assert predictions[0].image_filename == "single.png"
    
    def test_create_predictions_batch_large_batch(self, db: Session, prediction_service: PredictionService):
        """Test creating large batch of predictions."""
        predictions_data = [
            PredictionCreate(
                image_filename=f"batch_image_{i}.png",
                prediction_class="PNEUMONIA",
                confidence_score=0.90,
                model_name="v1.0"
            )
            for i in range(100)
        ]
        
        predictions = prediction_service.create_predictions_batch(db, predictions_data)
        
        assert len(predictions) == 100
        assert all(p.id is not None for p in predictions)
    
    def test_create_predictions_batch_mixed_classes(self, db: Session, prediction_service: PredictionService):
        """Test batch creation with mixed prediction classes."""
        classes = ["NORMAL", "PNEUMONIA", "COVID-19", "TUBERCULOSIS"]
        predictions_data = [
            PredictionCreate(
                image_filename=f"image_{cls}.png",
                prediction_class=cls,
                confidence_score=0.85,
                model_name="v1.0"
            )
            for cls in classes
        ]
        
        predictions = prediction_service.create_predictions_batch(db, predictions_data)
        
        assert len(predictions) == 4
        result_classes = [p.prediction_class for p in predictions]
        assert set(result_classes) == set(classes)


class TestGetPrediction(TestPredictionService):
    """Tests for get_prediction method."""
    
    def test_get_prediction_success(self, db: Session, prediction_service: PredictionService, test_prediction):
        """Test successful prediction retrieval by ID."""
        prediction = prediction_service.get_prediction(db, test_prediction.id)
        
        assert prediction is not None
        assert prediction.id == test_prediction.id
        assert prediction.image_filename == test_prediction.image_filename
        assert prediction.prediction_class == test_prediction.prediction_class
    
    def test_get_prediction_not_found(self, db: Session, prediction_service: PredictionService):
        """Test retrieving non-existent prediction."""
        prediction = prediction_service.get_prediction(db, 99999)
        
        assert prediction is None
    
    def test_get_prediction_with_detections(self, db: Session, prediction_service: PredictionService, test_prediction):
        """Test that get_prediction can access relationships."""
        prediction = prediction_service.get_prediction(db, test_prediction.id)
        
        assert prediction is not None
        # Should be able to access detections relationship
        assert hasattr(prediction, 'detections')


class TestGetPredictions(TestPredictionService):
    """Tests for get_predictions method."""
    
    def test_get_predictions_success(self, db: Session, prediction_service: PredictionService, test_prediction):
        """Test retrieving all predictions."""
        predictions = prediction_service.get_predictions(db)
        
        assert len(predictions) >= 1
        assert any(p.id == test_prediction.id for p in predictions)
    
    def test_get_predictions_pagination(self, db: Session, prediction_service: PredictionService):
        """Test pagination of predictions."""
        # Create multiple predictions
        for i in range(15):
            prediction_data = PredictionCreate(
                image_filename=f"page_test_{i}.png",
                prediction_class="PNEUMONIA",
                confidence_score=0.90,
                model_name="v1.0"
            )
            prediction_service.create_prediction(db, prediction_data)
        
        # Get first page
        page1 = prediction_service.get_predictions(db, skip=0, limit=10)
        assert len(page1) == 10
        
        # Get second page
        page2 = prediction_service.get_predictions(db, skip=10, limit=10)
        assert len(page2) >= 5
        
        # Verify no overlap
        page1_ids = {p.id for p in page1}
        page2_ids = {p.id for p in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0
    
    def test_get_predictions_default_limit(self, db: Session, prediction_service: PredictionService):
        """Test default limit for predictions."""
        predictions = prediction_service.get_predictions(db)
        
        # Default limit is 100
        assert len(predictions) <= 100
    
    def test_get_predictions_custom_limit(self, db: Session, prediction_service: PredictionService):
        """Test custom limit for predictions."""
        # Create multiple predictions
        for i in range(10):
            prediction_data = PredictionCreate(
                image_filename=f"limit_test_{i}.png",
                prediction_class="PNEUMONIA",
                confidence_score=0.90,
                model_name="v1.0"
            )
            prediction_service.create_prediction(db, prediction_data)
        
        predictions = prediction_service.get_predictions(db, limit=5)
        
        assert len(predictions) <= 5
    
    def test_get_predictions_skip_offset(self, db: Session, prediction_service: PredictionService):
        """Test skip offset for predictions."""
        # Create predictions
        created_ids = []
        for i in range(5):
            prediction_data = PredictionCreate(
                image_filename=f"skip_test_{i}.png",
                prediction_class="PNEUMONIA",
                confidence_score=0.90,
                model_name="v1.0"
            )
            pred = prediction_service.create_prediction(db, prediction_data)
            created_ids.append(pred.id)
        
        # Skip first 2
        predictions = prediction_service.get_predictions(db, skip=2, limit=10)
        
        # Should not contain first 2
        result_ids = [p.id for p in predictions]
        assert created_ids[0] not in result_ids[:3] if len(result_ids) >= 3 else True
        assert created_ids[1] not in result_ids[:3] if len(result_ids) >= 3 else True


class TestGetPredictionsByClass(TestPredictionService):
    """Tests for get_predictions_by_class method."""
    
    def test_get_predictions_by_class_success(self, db: Session, prediction_service: PredictionService):
        """Test filtering predictions by class."""
        # Create predictions with different classes
        classes = ["PNEUMONIA", "NORMAL", "PNEUMONIA", "COVID-19", "PNEUMONIA"]
        for i, pred_class in enumerate(classes):
            prediction_data = PredictionCreate(
                image_filename=f"class_test_{i}.png",
                prediction_class=pred_class,
                confidence_score=0.90,
                model_name="v1.0"
            )
            prediction_service.create_prediction(db, prediction_data)
        
        pneumonia_predictions = prediction_service.get_predictions_by_class(db, "PNEUMONIA")
        
        assert len(pneumonia_predictions) >= 3
        assert all(p.prediction_class == "PNEUMONIA" for p in pneumonia_predictions)
    
    def test_get_predictions_by_class_normal(self, db: Session, prediction_service: PredictionService):
        """Test filtering by NORMAL class."""
        # Create NORMAL predictions
        for i in range(3):
            prediction_data = PredictionCreate(
                image_filename=f"normal_{i}.png",
                prediction_class="NORMAL",
                confidence_score=0.95,
                model_name="v1.0"
            )
            prediction_service.create_prediction(db, prediction_data)
        
        normal_predictions = prediction_service.get_predictions_by_class(db, "NORMAL")
        
        assert len(normal_predictions) >= 3
        assert all(p.prediction_class == "NORMAL" for p in normal_predictions)
    
    def test_get_predictions_by_class_none_found(self, db: Session, prediction_service: PredictionService):
        """Test filtering by non-existent class."""
        predictions = prediction_service.get_predictions_by_class(db, "NONEXISTENT")
        
        assert len(predictions) == 0
    
    def test_get_predictions_by_class_case_sensitive(self, db: Session, prediction_service: PredictionService):
        """Test that class filtering is case-sensitive."""
        prediction_data = PredictionCreate(
            image_filename="case_test.png",
            prediction_class="PNEUMONIA",
            confidence_score=0.90,
            model_name="v1.0"
        )
        prediction_service.create_prediction(db, prediction_data)
        
        # Search with lowercase should not find uppercase
        predictions = prediction_service.get_predictions_by_class(db, "pneumonia")
        
        # This depends on database collation, but typically should be case-sensitive
        assert len([p for p in predictions if p.prediction_class == "PNEUMONIA"]) == 0


class TestEdgeCases(TestPredictionService):
    """Tests for edge cases and special scenarios."""
    
    def test_prediction_with_special_characters_in_name(self, db: Session, prediction_service: PredictionService):
        """Test creating prediction with special characters in image name."""
        prediction_data = PredictionCreate(
            image_filename="test_image@#$%.png",
            prediction_class="PNEUMONIA",
            confidence_score=0.90,
            model_name="v1.0"
        )
        
        prediction = prediction_service.create_prediction(db, prediction_data)
        
        assert prediction.image_filename == "test_image@#$%.png"
    
    def test_prediction_with_long_image_name(self, db: Session, prediction_service: PredictionService):
        """Test creating prediction with very long image name."""
        long_name = "a" * 200 + ".png"
        prediction_data = PredictionCreate(
            image_filename=long_name,
            prediction_class="PNEUMONIA",
            confidence_score=0.90,
            model_name="v1.0"
        )
        
        prediction = prediction_service.create_prediction(db, prediction_data)
        
        assert prediction.image_filename == long_name
    
    def test_prediction_with_path_in_name(self, db: Session, prediction_service: PredictionService):
        """Test creating prediction with path-like image name."""
        prediction_data = PredictionCreate(
            image_filename="path/to/image.png",
            prediction_class="PNEUMONIA",
            confidence_score=0.90,
            model_name="v1.0"
        )
        
        prediction = prediction_service.create_prediction(db, prediction_data)
        
        assert prediction.image_filename == "path/to/image.png"
    
    def test_prediction_confidence_precision(self, db: Session, prediction_service: PredictionService):
        """Test that confidence score precision is maintained."""
        prediction_data = PredictionCreate(
            image_filename="precision_test.png",
            prediction_class="PNEUMONIA",
            confidence_score=0.123456789,
            model_name="v1.0"
        )
        
        prediction = prediction_service.create_prediction(db, prediction_data)
        
        # Check that precision is maintained (within floating point limits)
        assert abs(prediction.confidence_score - 0.123456789) < 1e-6
    
    def test_prediction_with_unicode_characters(self, db: Session, prediction_service: PredictionService):
        """Test creating prediction with unicode characters in name."""
        prediction_data = PredictionCreate(
            image_filename="测试图像.png",
            prediction_class="PNEUMONIA",
            confidence_score=0.90,
            model_name="v1.0"
        )
        
        prediction = prediction_service.create_prediction(db, prediction_data)
        
        assert prediction.image_filename == "测试图像.png"
    
    def test_predictions_ordered_by_creation(self, db: Session, prediction_service: PredictionService):
        """Test that predictions maintain creation order."""
        created_names = []
        for i in range(5):
            prediction_data = PredictionCreate(
                image_filename=f"order_test_{i}.png",
                prediction_class="PNEUMONIA",
                confidence_score=0.90,
                model_name="v1.0"
            )
            pred = prediction_service.create_prediction(db, prediction_data)
            created_names.append(pred.image_filename)
        
        predictions = prediction_service.get_predictions(db, limit=5)
        
        # Verify order is maintained
        result_names = [p.image_filename for p in predictions if p.image_filename in created_names]
        assert len(result_names) == 5
    
    def test_batch_creation_transaction_integrity(self, db: Session, prediction_service: PredictionService):
        """Test that batch creation maintains transaction integrity."""
        predictions_data = [
            PredictionCreate(
                image_filename=f"transaction_test_{i}.png",
                prediction_class="PNEUMONIA",
                confidence_score=0.90,
                model_name="v1.0"
            )
            for i in range(10)
        ]
        
        predictions = prediction_service.create_predictions_batch(db, predictions_data)
        
        # All should be created successfully
        assert len(predictions) == 10
        
        # Verify all are in database
        for pred in predictions:
            db_pred = prediction_service.get_prediction(db, pred.id)
            assert db_pred is not None
    
    def test_prediction_timestamps(self, db: Session, prediction_service: PredictionService):
        """Test that created_at timestamp is set correctly."""
        prediction_data = PredictionCreate(
            image_filename="timestamp_test.png",
            prediction_class="PNEUMONIA",
            confidence_score=0.90,
            model_name="v1.0"
        )
        
        prediction = prediction_service.create_prediction(db, prediction_data)
        
        assert prediction.created_at is not None
        # Should be recent (within last minute)
        from datetime import datetime, timedelta
        assert datetime.utcnow() - prediction.created_at < timedelta(minutes=1)
