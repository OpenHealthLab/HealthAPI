"""
Error handling and edge case tests.

Tests for error scenarios, malformed data, and edge cases.
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


def test_cade_malformed_image():
    """Test CADe detection with corrupted image data."""
    corrupted_data = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"corrupted")
    
    response = client.post(
        "/api/v1/cade/detect",
        files={"file": ("corrupted.png", corrupted_data, "image/png")}
    )
    
    assert response.status_code in [400, 422, 500]


def test_invalid_content_type():
    """Test with invalid content type header."""
    valid_image = io.BytesIO(b"fake image data")
    
    response = client.post(
        "/api/v1/predict",
        files={"file": ("test.exe", valid_image, "application/x-msdownload")}
    )
    
    assert response.status_code in [400, 422]


def test_missing_required_parameters():
    """Test API calls with missing required parameters."""
    # Test predict without file
    response = client.post("/api/v1/predict")
    assert response.status_code == 422
    
    # Test CADe detect without file
    response = client.post("/api/v1/cade/detect")
    assert response.status_code == 422
