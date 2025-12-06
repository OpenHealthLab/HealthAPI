import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_logging_headers_presence():
    """
    Test that every response contains the custom tracking headers
    added by the LoggingMiddleware.
    """
    # Use a known endpoint like /docs to ensure a 200 OK
    response = client.get("/docs")
    
    assert response.status_code == 200
    
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0
    
    assert "X-Process-Time" in response.headers
    assert float(response.headers["X-Process-Time"]) >= 0

def test_sensitive_data_masking(caplog):
    """
    Test that the Authorization header is masked in the logs.
    'caplog' is a pytest fixture that captures log output.
    """
    client.get(
        "/docs", 
        headers={"Authorization": "Bearer SECRET_TOKEN_123"}
    )
    
    logs = caplog.text
    
    # Ensure sensitive data is not logged
    assert "SECRET_TOKEN_123" not in logs
    assert "***MASKED***" in logs