"""
Data validation and schema tests.

Tests for response schemas, data types, and field validation.
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
