"""
CADe detection endpoint tests.

Tests for Computer-Aided Detection (CADe) functionality for single and batch images.
"""

import pytest
from fastapi.testclient import TestClient
import io
from PIL import Image

from app.main import app

# Use the test client with the proper fixtures from conftest.py
client = TestClient(app)


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
# SINGLE CADe DETECTION TESTS
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
# BATCH CADe DETECTION TESTS
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
