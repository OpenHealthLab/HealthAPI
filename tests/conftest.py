"""
Pytest configuration and fixtures for integration tests.

Provides database setup/teardown and common test fixtures.
"""

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Import Base and all models to ensure they're registered
from app.core.database import Base, get_db
from app.models.user import User, Role, UserRole, Session as SessionModel, AuditLog
from app.main import app
from app.core.casbin_enforcer import casbin_enforcer
from app.schemas.role import RoleCreate
from app.api.dependencies import limiter


# Use in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    """
    Create a test database engine for each test function.
    Uses an in-memory SQLite database.
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Required for in-memory SQLite with multiple connections
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db(test_engine):
    """
    Create a test database session for each test function.
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function", autouse=True)
def override_get_db(test_engine):
    """
    Override the get_db dependency to use the test database.
    This is automatically used for all tests.
    Also seeds initial roles and initializes Casbin enforcer.
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    def _get_test_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    # Override the dependency
    app.dependency_overrides[get_db] = _get_test_db
    
    # Seed essential roles for testing
    db = TestingSessionLocal()
    try:
        essential_roles = [
            {"name": "api_user", "display_name": "API User", "description": "Default API user role", "is_system_role": False},
            {"name": "admin", "display_name": "Administrator", "description": "Full access admin role", "is_system_role": True},
            {"name": "doctor", "display_name": "Doctor", "description": "Medical doctor role", "is_system_role": False},
            {"name": "radiologist", "display_name": "Radiologist", "description": "Radiology specialist", "is_system_role": False},
        ]
        for role_data in essential_roles:
            role = Role(
                name=role_data["name"],
                display_name=role_data["display_name"],
                description=role_data["description"],
                is_system_role=role_data["is_system_role"]
            )
            db.add(role)
        db.commit()
    finally:
        db.close()
    
    # Initialize Casbin enforcer
    try:
        if not casbin_enforcer.enforcer:
            casbin_enforcer.initialize()
    except:
        pass  # Casbin might already be initialized
    
    yield
    
    # Clean up override after test
    app.dependency_overrides.clear()


@pytest.fixture(scope="function", autouse=True)
def reset_limiter():
    """
    Reset the rate limiter state before each test.
    This prevents rate limit state from persisting across tests.
    """
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def anyio_backend():
    """AnyIO backend for async pytest support."""
    return "asyncio"
