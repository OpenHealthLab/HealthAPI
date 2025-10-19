"""
V2 API User management tests.

Tests for protected user endpoints and user information retrieval.
"""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.fixture
def anyio_backend():
    """AnyIO backend for async pytest support."""
    return "asyncio"


@pytest.fixture
async def registered_user():
    """
    Register a test user and obtain a JWT access token.
    Returns a dict with ``token`` and ``username``.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register
        register_payload = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "StrongP@ssw0rd!"
        }
        reg_resp = await client.post("/api/v2/auth/register", json=register_payload)
        assert reg_resp.status_code == 201, f"Register failed: {reg_resp.text}"

        # Login
        login_payload = {
            "username": "testuser",
            "password": "StrongP@ssw0rd!"
        }
        login_resp = await client.post("/api/v2/auth/login", json=login_payload)
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        return {"token": token, "username": register_payload["username"]}


@pytest.mark.anyio
async def test_protected_user_endpoint(registered_user):
    """
    Verify that an authenticated request can access ``/api/v2/users/me``.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {registered_user['token']}"}
        resp = await client.get("/api/v2/users/me", headers=headers)
        assert resp.status_code == 200, f"Protected endpoint failed: {resp.text}"
        data = resp.json()
        assert data["username"] == registered_user["username"]


@pytest.mark.anyio
async def test_protected_endpoint_without_token():
    """Test that protected endpoint requires authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/v2/users/me")
        assert resp.status_code in [401, 403]


@pytest.mark.anyio
async def test_protected_endpoint_with_invalid_token():
    """Test protected endpoint with invalid token."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": "Bearer invalid_token_here"}
        resp = await client.get("/api/v2/users/me", headers=headers)
        assert resp.status_code in [401, 403]
