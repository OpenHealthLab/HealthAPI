import time
from fastapi import APIRouter, status, Response
from datetime import datetime, timezone
from sqlalchemy import text
from app.schemas.prediction import HealthCheck, DependencyStatus
from app.core.config import get_settings
from app.ml.inference import ModelInference
from app.core.database import SessionLocal
from app.core.logging_config import get_logger

router = APIRouter()
start_time = time.time()
logger = get_logger(__name__)

def check_database_connection() -> bool:
    """Check if database is reachable"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}", exc_info=True)
        return False


def check_model_loaded() -> bool:
    """Check if ML model is loaded"""
    model_inference = ModelInference()
    model_inference.load_model()
    return model_inference.model_loaded


@router.get("/health", response_model=HealthCheck)
async def health_check(response: Response):
    """Enhanced health check endpoint with comprehensive status information"""
    
    settings = get_settings()
    db_status = check_database_connection()
    model_status = check_model_loaded()
    response.status_code = status.HTTP_200_OK if (db_status and model_status) else status.HTTP_503_SERVICE_UNAVAILABLE
    
    current_time = time.time()

    return HealthCheck(
        status="healthy" if (db_status and model_status) else "unhealthy",
        app_name=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=current_time - start_time,
        dependencies={
            "database":DependencyStatus.OK if db_status else DependencyStatus.ERROR,
            "model":DependencyStatus.OK if model_status else DependencyStatus.ERROR,
        }
    )


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Healthcare AI Backend API",
        "docs": "/docs",
        "health": "/api/v1/health"
    }
