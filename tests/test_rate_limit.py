import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_rate_limiting_login():

    url = "/api/v2/auth/login"
    payload = {"username": "test_limit_user", "password": "wrong_password"}

    for i in range(5):
        response = client.post(url, json=payload)
        assert response.status_code != 429, f"Request {i+1} was blocked too early!"

    response = client.post(url, json=payload)
    
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]
