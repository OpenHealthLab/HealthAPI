import logging
from datetime import datetime, timezone
import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.prediction import HealthCheck
from app.core.config import get_settings
from app.ml.inference import ModelInference
from app.core.database import SessionLocal

# Import start_time from app.main. This relies on `app.main` executing
# and defining `start_time` at the module level *before* `health.py` is fully loaded,
# which is typically the case when `app.main` is the entry point and imports this module.
# While functional, relying on global variables from other modules can make testing
# more challenging and introduces tight coupling. For new work, consider explicit
# dependency injection or FastAPI's app state for such application-wide values.
from app.main import start_time as app_start_time

router = APIRouter()
model_inference = ModelInference()

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Define constants for dependency statuses for consistency and typo prevention
DB_STATUS_CONNECTED = "connected"
DB_STATUS_DISCONNECTED = "disconnected"
MODEL_STATUS_LOADED = "loaded"
MODEL_STATUS_NOT_LOADED = "not loaded"

async def get_db_status() -> Dict[str, Any]:
    """
    Checks the database connection status by attempting a trivial query.
    Returns a dictionary with status and an optional error message.
    """
    try:
        # Use a context manager for the session to ensure it's closed and released
        # back to the connection pool, even if an error occurs.
        with SessionLocal() as db_session:
            # Execute a trivial query directly on the session.
            # This confirms the session can acquire a connection and interact with the DB.
            db_session.execute(text("SELECT 1"))
        return {"status": DB_STATUS_CONNECTED}
    except SQLAlchemyError as e:
        # Catch specific SQLAlchemy errors for better error differentiation
        error_msg = f"Database connection error: {type(e).__name__} - {e}"
        logger.error("Database health check failed: %s", error_msg)
        return {"status": DB_STATUS_DISCONNECTED, "error": error_msg}
    except Exception as e:
        # Catch any other unexpected exceptions during the DB check
        error_msg = f"An unexpected error occurred during database health check: {type(e).__name__} - {e}"
        logger.error("Database health check encountered an unexpected error: %s", error_msg)
        return {"status": DB_STATUS_DISCONNECTED, "error": error_msg}

@router.get("/health", response_model=HealthCheck, summary="Application Health Check")
async def health_check():
    """
    Provides a detailed health check for the application, including:
    
    - `version`: The current application version as configured.
    - `timestamp`: The current UTC timestamp when the check was performed.
    - `uptime_seconds`: The total number of seconds the application has been running since startup.
    - `dependencies`: A dictionary containing the status of critical external dependencies,
      such as the database and the machine learning model.
      
    Returns:
    - `HTTP 200 OK`: If all critical dependencies are healthy.
    - `HTTP 503 SERVICE UNAVAILABLE`: If any critical dependency is unhealthy,
      with a detailed status in the response body.
    """
    settings = get_settings()
    
    # Use timezone-aware datetime for current timestamp, adhering to best practices.
    current_timestamp = datetime.now(timezone.utc)
    
    # Calculate application uptime based on the global start_time
    uptime_seconds = time.time() - app_start_time

    # Perform database health check
    db_dependency_status = await get_db_status()

    # Determine ML model status
    model_dependency_status = {
        "status": MODEL_STATUS_LOADED if model_inference.model_loaded else MODEL_STATUS_NOT_LOADED
    }
    
    # Determine overall health based on critical dependencies
    is_healthy = (
        db_dependency_status["status"] == DB_STATUS_CONNECTED and 
        model_inference.model_loaded
    )
    
    dependencies_info = {
        "database": db_dependency_status,
        "model": model_dependency_status
    }
    
    # Construct the health check response model
    response_content = HealthCheck(
        version=settings.app_version,
        timestamp=current_timestamp,
        uptime_seconds=uptime_seconds,
        dependencies=dependencies_info
    )

    if not is_healthy:
        # Log a warning if the health check indicates an issue, crucial for operations monitoring
        logger.warning(
            "Health check failed. Overall status: unhealthy. Database: %s, Model: %s",
            db_dependency_status["status"],
            model_dependency_status["status"]
        )
        # Raise an HTTPException with 503 status code and the detailed health information.
        # .model_dump(mode='json') provides a dictionary representation compatible with JSON serialization.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response_content.model_dump(mode='json')
        )
    
    # Log successful health check
    logger.info("Health check successful. All critical dependencies are healthy.")
    return response_content

@router.get("/", summary="Root API Endpoint")
async def root():
    """
    Provides basic information about the API and links to documentation and health check.
    """
    return {
        "message": "Healthcare AI Backend API",
        "docs": "/docs",
        "health": "/health"
    }