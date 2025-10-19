"""
V2 API Authentication tests.

Tests for user registration, login, and rate limiting.
"""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.fixture
def anyio_backend():
    """AnyIO backend for async pytest support."""
    return "asyncio"


@pytest.mark.anyio
async def test_user_registration():
    """Test user registration endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        register_payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongP@ssw0rd!"
        }
        response = await client.post("/api/v2/auth/register", json=register_payload)
        assert response.status_code == 201, f"Register failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"


@pytest.mark.anyio
async def test_user_login():
    """Test user login endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register first
        register_payload = {
            "username": "loginuser",
            "email": "loginuser@example.com",
            "password": "StrongP@ssw0rd!"
        }
        await client.post("/api/v2/auth/register", json=register_payload)
        
        # Now login
        login_payload = {
            "username": "loginuser",
            "password": "StrongP@ssw0rd!"
        }
        response = await client.post("/api/v2/auth/login", json=login_payload)
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        login_payload = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        response = await client.post("/api/v2/auth/login", json=login_payload)
        assert response.status_code == 401


@pytest.mark.anyio
async def test_login_rate_limit():
    """
    The login endpoint is limited to 5 requests per minute.
    The sixth rapid request should receive a 429 response.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        login_payload = {"username": "nonexistent", "password": "invalid"}
        # Perform 5 allowed attempts
        for _ in range(5):
            resp = await client.post("/api/v2/auth/login", json=login_payload)
            # These may return 401 (invalid credentials) but must NOT be 429
            assert resp.status_code != 429, f"Rate limit triggered too early: {resp.text}"
        # Sixth attempt should be rate-limited
        resp = await client.post("/api/v2/auth/login", json=login_payload)
        assert resp.status_code == 429, f"Expected 429 Too Many Requests, got {resp.status_code}"
