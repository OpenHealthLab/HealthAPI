"""
Batch prediction endpoint tests.

Tests for multiple image batch prediction functionality.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys
import io
from PIL import Image

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
