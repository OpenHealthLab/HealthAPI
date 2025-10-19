"""
CADe detection retrieval tests.

Tests for retrieving, filtering, and paginating CADe detection results.
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
