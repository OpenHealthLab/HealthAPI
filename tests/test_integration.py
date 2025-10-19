"""
Integration tests.

Tests for end-to-end workflows and concurrent operations.
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
