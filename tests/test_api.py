"""
API endpoint tests.

This module contains comprehensive tests for the FastAPI endpoints to ensure
they work correctly and handle edge cases properly.

Run tests with:
    pytest tests/test_api.py -v
    
Run with coverage:
    pytest tests/test_api.py --cov=app --cov-report=html
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys
import io
from PIL import Image
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app, container
from app.core.database import Base, get_db

# Test database configuration
# Use in-memory SQLite for faster tests
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(TEST_DIR, 'test.db')}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
# Note: The DI container is already initialized in app.main
# If you need to mock ML models or services, use:
# with container.override_providers(...):
#     # run tests
# Or create fixtures with container overrides
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """
    Set up and tear down test database for each test.
    
    This fixture automatically runs before and after each test,
    ensuring a clean database state.
    """
    # Setup: Create all tables
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown: Drop all tables and remove database file
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test.db"):
        os.remove("test.db")


def create_test_image(format="PNG", size=(224, 224), color="RGB"):
    """
    Create a test image in memory.
    
    Args:
        format: Image format (PNG, JPEG)
        size: Image dimensions (width, height)
        color: Color mode (RGB, L)
    
    Returns:
        BytesIO object containing the image
    """
    image = Image.new(color, size, color=(100, 100, 100))
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format=format)
    img_byte_arr.seek(0)
    return img_byte_arr


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================


def test_read_root():
    """Test the root endpoint returns a welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "health" in data
    assert data["message"] == "Healthcare AI Backend API"


def test_health_check():
    """Test the health check endpoint returns correct status."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    print('data 007', data)
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "version" in data
    assert "model_loaded" in data
    assert isinstance(data["model_loaded"], bool)
    assert data["app_name"] == "Healthcare AI Backend"


# ============================================================================
# PREDICTION ENDPOINT TESTS
# ============================================================================


def test_get_predictions_empty():
    """Test getting predictions when database is empty."""
    response = client.get("/api/v1/predictions")
    assert response.status_code == 200
    assert response.json() == []


def test_predict_chest_xray_success():
    """Test successful chest X-ray prediction with valid image."""
    img = create_test_image(format="PNG", size=(224, 224))
    
    response = client.post(
        "/api/v1/predict",
        files={"file": ("test_xray.png", img, "image/png")}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify response structure
    assert "id" in data
    assert "image_filename" in data
    assert "model_name" in data
    assert "prediction_class" in data
    assert "confidence_score" in data
    assert "processing_time" in data
    assert "created_at" in data
    
    # Verify data types
    assert isinstance(data["id"], int)
    assert isinstance(data["confidence_score"], float)
    assert 0.0 <= data["confidence_score"] <= 1.0
    
    # Check filename has correct extension (UUID-based naming)
    assert data["image_filename"].endswith(".png")



def test_predict_chest_xray_jpeg():
    """Test prediction with JPEG image format."""
    img = create_test_image(format="JPEG", size=(512, 512))
    
    response = client.post(
        "/api/v1/predict",
        files={"file": ("chest_xray.jpg", img, "image/jpeg")}
    )
    
    assert response.status_code == 201
    data = response.json()
    print(data)
    # Check filename has correct extension instead of exact match
    assert data["image_filename"].endswith(".jpg")
    
    # Verify it's a UUID-based filename
    import re
    uuid_pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\.(jpg|jpeg)$'
    assert re.match(uuid_pattern, data["image_filename"])


def test_predict_chest_xray_no_file():
    """Test prediction endpoint without file upload."""
    response = client.post("/api/v1/predict")
    assert response.status_code == 422


def test_predict_chest_xray_invalid_format():
    """Test prediction with invalid file format."""
    invalid_file = io.BytesIO(b"This is not an image")
    
    response = client.post(
        "/api/v1/predict",
        files={"file": ("test.txt", invalid_file, "text/plain")}
    )
    
    # Should return error (400 or 422)
    assert response.status_code in [400, 422]


def test_predict_chest_xray_small_image():
    """Test prediction with very small image."""
    img = create_test_image(format="PNG", size=(32, 32))
    
    response = client.post(
        "/api/v1/predict",
        files={"file": ("small_xray.png", img, "image/png")}
    )
    
    # Should either succeed or fail gracefully
    assert response.status_code in [201, 400, 422]


def test_get_predictions_with_pagination():
    """Test getting predictions with pagination parameters."""
    # Create some test predictions first
    for i in range(5):
        img = create_test_image()
        client.post(
            "/api/v1/predict",
            files={"file": (f"test_{i}.png", img, "image/png")}
        )
    
    # Test with pagination
    response = client.get("/api/v1/predictions?skip=0&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 3
    
    # Test skip parameter
    response = client.get("/api/v1/predictions?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2

# ============================================================================
# BATCH PREDICTION TESTS
# ============================================================================


def test_predict_batch_success():
    """Test successful batch prediction with multiple images."""
    files = [
        ("files", (f"xray_{i}.png", create_test_image(), "image/png"))
        for i in range(3)
    ]
    
    response = client.post("/api/v1/predict/batch", files=files)
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify batch response structure
    assert "total_images" in data
    assert "successful" in data
    assert "failed" in data
    assert "total_processing_time" in data
    assert "predictions" in data
    assert "errors" in data
    
    # Verify counts
    assert data["total_images"] == 3
    assert data["successful"] >= 0
    assert data["failed"] >= 0
    assert data["successful"] + data["failed"] == data["total_images"]
    assert isinstance(data["predictions"], list)


def test_predict_batch_empty():
    """Test batch prediction with no files."""
    response = client.post("/api/v1/predict/batch", files=[])
    assert response.status_code == 422


def test_predict_batch_max_limit():
    """Test batch prediction with maximum allowed images (50)."""
    files = [
        ("files", (f"xray_{i}.png", create_test_image(), "image/png"))
        for i in range(50)
    ]
    
    response = client.post("/api/v1/predict/batch", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["total_images"] == 50


def test_predict_batch_exceed_limit():
    """Test batch prediction exceeding maximum limit."""
    files = [
        ("files", (f"xray_{i}.png", create_test_image(), "image/png"))
        for i in range(51)
    ]
    
    response = client.post("/api/v1/predict/batch", files=files)
    # Should return error (400 or 422)
    assert response.status_code in [400, 422]


def test_predict_batch_mixed_formats():
    """Test batch prediction with mixed image formats."""
    files = [
        ("files", ("xray_1.png", create_test_image(format="PNG"), "image/png")),
        ("files", ("xray_2.jpg", create_test_image(format="JPEG"), "image/jpeg")),
        ("files", ("xray_3.png", create_test_image(format="PNG"), "image/png")),
    ]
    
    response = client.post("/api/v1/predict/batch", files=files)
    assert response.status_code == 201


def test_predict_batch_partial_failure():
    """Test batch prediction with some invalid files."""
    files = [
        ("files", ("valid.png", create_test_image(), "image/png")),
        ("files", ("invalid.txt", io.BytesIO(b"invalid"), "text/plain")),
    ]
    
    response = client.post("/api/v1/predict/batch", files=files)
    
    # Should still return 201 with error details
    assert response.status_code == 201
    data = response.json()
    assert data["failed"] >= 1
    assert len(data["errors"]) >= 1


# ============================================================================
# CADe DETECTION TESTS
# ============================================================================


def test_cade_detect_success():
    """Test successful CADe detection on chest X-ray."""
    img = create_test_image(format="PNG", size=(512, 512))
    
    response = client.post(
        "/api/v1/cade/detect",
        files={"file": ("xray.png", img, "image/png")}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify CADe response structure
    assert "prediction_id" in data
    assert "image_filename" in data
    assert "model_name" in data
    assert "num_findings" in data
    assert "processing_time" in data
    assert "detections" in data
    
    assert isinstance(data["num_findings"], int)
    assert isinstance(data["detections"], list)
    assert data["num_findings"] == len(data["detections"])


def test_cade_detect_no_file():
    """Test CADe detection without file."""
    response = client.post("/api/v1/cade/detect")
    assert response.status_code == 422


def test_cade_detect_invalid_file():
    """Test CADe detection with invalid file format."""
    invalid_file = io.BytesIO(b"Not an image")
    
    response = client.post(
        "/api/v1/cade/detect",
        files={"file": ("test.txt", invalid_file, "text/plain")}
    )
    
    assert response.status_code in [400, 422]


def test_cade_detection_bounding_boxes():
    """Test that detections contain valid bounding boxes."""
    img = create_test_image(format="PNG")
    
    response = client.post(
        "/api/v1/cade/detect",
        files={"file": ("xray.png", img, "image/png")}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    for detection in data["detections"]:
        assert "id" in detection
        assert "prediction_id" in detection
        assert "finding_type" in detection
        assert "confidence_score" in detection
        assert "bounding_box" in detection
        assert "created_at" in detection
        
        # Verify bounding box structure
        bbox = detection["bounding_box"]
        assert "x1" in bbox
        assert "y1" in bbox
        assert "x2" in bbox
        assert "y2" in bbox
        
        # Verify normalized coordinates (0-1 range)
        assert 0.0 <= bbox["x1"] <= 1.0
        assert 0.0 <= bbox["y1"] <= 1.0
        assert 0.0 <= bbox["x2"] <= 1.0
        assert 0.0 <= bbox["y2"] <= 1.0
        
        # Verify confidence score
        assert 0.0 <= detection["confidence_score"] <= 1.0


# ============================================================================
# CADe BATCH DETECTION TESTS
# ============================================================================


def test_cade_detect_batch_success():
    """Test successful batch CADe detection."""
    files = [
        ("files", (f"xray_{i}.png", create_test_image(), "image/png"))
        for i in range(3)
    ]
    
    response = client.post("/api/v1/cade/detect/batch", files=files)
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify batch CADe response structure
    assert "total_images" in data
    assert "successful" in data
    assert "failed" in data
    assert "total_processing_time" in data
    assert "results" in data
    assert "errors" in data
    
    assert data["total_images"] == 3
    assert isinstance(data["results"], list)


def test_cade_detect_batch_empty():
    """Test batch CADe detection with no files."""
    response = client.post("/api/v1/cade/detect/batch", files=[])
    assert response.status_code == 422


def test_cade_detect_batch_max_limit():
    """Test batch CADe detection with 50 images."""
    files = [
        ("files", (f"xray_{i}.png", create_test_image(), "image/png"))
        for i in range(50)
    ]
    
    response = client.post("/api/v1/cade/detect/batch", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["total_images"] == 50


# ============================================================================
# CADe RETRIEVAL TESTS
# ============================================================================


def test_get_detections_for_prediction():
    """Test retrieving detections for a specific prediction."""
    # First create a prediction with detection
    img = create_test_image()
    pred_response = client.post(
        "/api/v1/cade/detect",
        files={"file": ("xray.png", img, "image/png")}
    )
    
    assert pred_response.status_code == 201
    prediction_id = pred_response.json()["prediction_id"]
    
    # Now get detections for that prediction
    response = client.get(f"/api/v1/cade/detections/{prediction_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_get_detections_for_nonexistent_prediction():
    """Test retrieving detections for non-existent prediction ID."""
    response = client.get("/api/v1/cade/detections/99999")
    assert response.status_code in [200, 404]
    
    if response.status_code == 200:
        assert response.json() == []


def test_get_all_detections_empty():
    """Test getting all detections when database is empty."""
    response = client.get("/api/v1/cade/detections")
    assert response.status_code == 200
    assert response.json() == []


def test_get_all_detections_with_pagination():
    """Test getting all detections with pagination."""
    # Create some detections
    for i in range(5):
        img = create_test_image()
        client.post(
            "/api/v1/cade/detect",
            files={"file": (f"xray_{i}.png", img, "image/png")}
        )
    
    # Test pagination
    response = client.get("/api/v1/cade/detections?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Test with skip
    response = client.get("/api/v1/cade/detections?skip=2&limit=5")
    assert response.status_code == 200


def test_get_all_detections_with_filter():
    """Test filtering detections by finding type."""
    response = client.get("/api/v1/cade/detections?finding_type=Pneumothorax")
    assert response.status_code == 200
    data = response.json()
    
    # Verify all returned detections match the filter
    for detection in data:
        assert detection["finding_type"] == "Pneumothorax"


def test_get_all_detections_invalid_pagination():
    """Test detections endpoint with invalid pagination."""
    response = client.get("/api/v1/cade/detections?skip=-1")
    assert response.status_code == 422
    
    response = client.get("/api/v1/cade/detections?limit=501")
    assert response.status_code == 422
    
    response = client.get("/api/v1/cade/detections?limit=0")
    assert response.status_code == 422


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_end_to_end_prediction_workflow():
    """Test complete workflow: predict -> retrieve -> verify."""
    # Step 1: Upload and predict
    img = create_test_image()
    pred_response = client.post(
        "/api/v1/predict",
        files={"file": ("test.png", img, "image/png")}
    )
    
    assert pred_response.status_code == 201
    prediction_id = pred_response.json()["id"]
    
    # Step 2: Retrieve all predictions
    list_response = client.get("/api/v1/predictions")
    assert list_response.status_code == 200
    predictions = list_response.json()
    
    # Step 3: Verify our prediction is in the list
    prediction_ids = [p["id"] for p in predictions]
    assert prediction_id in prediction_ids


def test_end_to_end_cade_workflow():
    """Test complete CADe workflow: detect -> retrieve -> verify."""
    # Step 1: Run detection
    img = create_test_image()
    detect_response = client.post(
        "/api/v1/cade/detect",
        files={"file": ("xray.png", img, "image/png")}
    )
    
    assert detect_response.status_code == 201
    prediction_id = detect_response.json()["prediction_id"]
    
    # Step 2: Retrieve detections for that prediction
    det_response = client.get(f"/api/v1/cade/detections/{prediction_id}")
    assert det_response.status_code == 200
    
    # Step 3: Retrieve all detections
    all_det_response = client.get("/api/v1/cade/detections")
    assert all_det_response.status_code == 200


def test_concurrent_predictions():
    """Test handling multiple concurrent prediction requests."""
    files = [
        ("file", (f"xray_{i}.png", create_test_image(), "image/png"))
        for i in range(5)
    ]
    
    responses = []
    for file_tuple in files:
        response = client.post("/api/v1/predict", files=[file_tuple])
        responses.append(response)
    
    # All should succeed
    for response in responses:
        assert response.status_code == 201


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


def test_malformed_image_data():
    """Test handling of corrupted image data."""
    corrupted_data = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"corrupted data")
    
    response = client.post(
        "/api/v1/predict",
        files={"file": ("corrupted.png", corrupted_data, "image/png")}
    )
    
    assert response.status_code in [400, 422, 500]


def test_empty_file():
    """Test handling of empty file upload."""
    empty_file = io.BytesIO(b"")
    
    response = client.post(
        "/api/v1/predict",
        files={"file": ("empty.png", empty_file, "image/png")}
    )
    
    assert response.status_code in [400, 422]


def test_large_image():
    """Test handling of very large image."""
    # Create a large image (4K resolution)
    large_img = create_test_image(format="PNG", size=(3840, 2160))
    
    response = client.post(
        "/api/v1/predict",
        files={"file": ("large.png", large_img, "image/png")}
    )
    
    # Should either succeed or fail gracefully
    assert response.status_code in [201, 400, 413, 422]


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


def test_batch_processing_time():
    """Verify batch processing returns timing information."""
    files = [
        ("files", (f"xray_{i}.png", create_test_image(), "image/png"))
        for i in range(5)
    ]
    
    response = client.post("/api/v1/predict/batch", files=files)
    assert response.status_code == 201
    
    data = response.json()
    assert "total_processing_time" in data
    assert data["total_processing_time"] > 0
    
    # Each prediction should have processing time
    for pred in data["predictions"]:
        assert "processing_time" in pred


def test_single_prediction_timing():
    """Verify individual predictions include timing."""
    img = create_test_image()
    response = client.post(
        "/api/v1/predict",
        files={"file": ("xray.png", img, "image/png")}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "processing_time" in data
    if data["processing_time"] is not None:
        assert data["processing_time"] > 0


# ============================================================================
# DATA VALIDATION TESTS
# ============================================================================


def test_prediction_response_schema():
    """Verify prediction response matches expected schema."""
    img = create_test_image()
    response = client.post(
        "/api/v1/predict",
        files={"file": ("test.png", img, "image/png")}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    required_fields = [
        "id", "image_filename", "model_name", "prediction_class",
        "confidence_score", "created_at"
    ]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Validate created_at is ISO format datetime
    try:
        datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
    except ValueError:
        pytest.fail("created_at is not valid ISO datetime format")


def test_cade_response_schema():
    """Verify CADe response matches expected schema."""
    img = create_test_image()
    response = client.post(
        "/api/v1/cade/detect",
        files={"file": ("xray.png", img, "image/png")}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    required_fields = [
        "prediction_id", "image_filename", "model_name",
        "num_findings", "processing_time", "detections"
    ]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
