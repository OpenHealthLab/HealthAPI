"""
Single prediction endpoint tests.

Tests for individual image prediction functionality.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys
import io
from PIL import Image
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.core.database import Base, get_db

# Test database configuration
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


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Set up and tear down test database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
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
    
    # Check filename has correct extension instead of exact match
    assert data["image_filename"].endswith(".jpg")
    
    # Verify it's a UUID-based filename
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
