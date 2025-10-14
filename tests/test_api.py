"""
API endpoint tests.

This module contains tests for the FastAPI endpoints to ensure
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

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.core.database import Base, get_db

# Test database configuration
# Use in-memory SQLite for faster tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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


def test_read_root():
    """Test the root endpoint returns a welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    """Test the health check endpoint returns correct status."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "version" in data
    assert "model_loaded" in data
    assert isinstance(data["model_loaded"], bool)


def test_get_predictions_empty():
    """Test getting predictions when database is empty."""
    response = client.get("/api/v1/predictions")
    assert response.status_code == 200
    assert response.json() == []


def test_get_predictions_with_pagination():
    """Test pagination parameters for predictions endpoint."""
    # Test with skip and limit parameters
    response = client.get("/api/v1/predictions?skip=0&limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# TODO: Add more tests
# - test_predict_with_valid_image()
# - test_predict_with_invalid_image()
# - test_predict_with_large_file()
# - test_get_prediction_by_id()
# - test_api_key_authentication()
