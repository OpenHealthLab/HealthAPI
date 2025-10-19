"""
Health check endpoint tests.

Tests the root endpoint and health check endpoint functionality.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.core.database import get_db
from tests.conftest import override_get_db

client = TestClient(app)


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
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "version" in data
    assert "model_loaded" in data
    assert isinstance(data["model_loaded"], bool)
    assert data["app_name"] == "Healthcare AI Backend"
