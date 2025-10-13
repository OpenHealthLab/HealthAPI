from fastapi import APIRouter
from app.schemas.prediction import HealthCheck
from app.core.config import get_settings
from app.ml.inference import ModelInference

router = APIRouter()
model_inference = ModelInference()

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    settings = get_settings()
    return HealthCheck(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        model_loaded=model_inference.model_loaded
    )

@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Healthcare AI Backend API",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

