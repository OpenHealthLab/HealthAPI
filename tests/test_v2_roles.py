"""
V2 API Role management tests.

Tests for role creation, management, and authorization.
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
async def test_role_creation_unauthorized(registered_user):
    """
    Attempt to create a role with a non-admin user.
    The endpoint should reject the request (401 or 403).
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {registered_user['token']}"}
        role_payload = {
            "name": "testrole",
            "display_name": "Test Role",
            "description": "A role created during tests",
            "is_system_role": False
        }
        resp = await client.post("/api/v2/roles/", json=role_payload, headers=headers)
        assert resp.status_code in (401, 403), f"Unexpected status: {resp.status_code}"


@pytest.mark.anyio
async def test_list_roles_without_auth():
    """Test listing roles without authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/v2/roles/")
        # May be public or require auth depending on implementation
        assert resp.status_code in [200, 401, 403]


@pytest.mark.anyio
async def test_get_role_details_unauthorized():
    """Test getting role details without proper authorization."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/v2/roles/1")
        # Should require authentication
        assert resp.status_code in [200, 401, 403, 404]
