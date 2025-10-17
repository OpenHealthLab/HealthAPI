"""
Main FastAPI application module.

This is the entry point for the Healthcare AI Backend API.
It configures the FastAPI app, middleware, and routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import engine, Base
from app.core.logging_config import LoggerSetup, get_logger
from app.api.routes import health, predictions, cade
from app.ml.inference import ModelInference
from app.ml.detection_inference import DetectionInference

settings = get_settings()

# Initialize logging system
LoggerSetup.setup_logging(
    log_level=settings.log_level,
    log_file=settings.log_file,
    log_dir="logs"
)
logger = get_logger(__name__)

model_inference = ModelInference()
detection_inference = DetectionInference()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    This function handles initialization tasks when the application starts
    and cleanup tasks when it shuts down.
    
    Startup tasks:
        - Create database tables
        - Load ML model into memory
        
    Shutdown tasks:
        - Clean up resources (if needed)
        
    Args:
        app: FastAPI application instance
        
    Yields:
        None: Control back to FastAPI during application runtime
    """
    # Startup
    logger.info("=" * 60)
    logger.info("🏥 Starting Healthcare AI Backend...")
    logger.info("=" * 60)
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}", exc_info=True)
        raise
    
    # Load ML models
    try:
        model_inference.load_model()
        logger.info("✓ Classification model loaded successfully")
    except Exception as e:
        logger.warning(f"Could not load classification model: {e}")
        logger.warning("The API will start but predictions may not work correctly")
    
    try:
        detection_inference.load_model()
        logger.info("✓ Detection model loaded successfully")
    except Exception as e:
        logger.warning(f"Could not load detection model: {e}")
        logger.warning("The API will start but CADe may use mock detections")
    
    logger.info("=" * 60)
    logger.info(f"🚀 Server ready at http://{settings.host}:{settings.port}")
    logger.info(f"📚 API docs at http://{settings.host}:{settings.port}/docs")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("👋 Shutting down Healthcare AI Backend...")
    logger.info("=" * 60)


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="REST API for Healthcare AI Models - Chest X-Ray Analysis",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS middleware
# In production, replace ["*"] with specific allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    health.router,
    tags=["Health"]
)

app.include_router(
    predictions.router,
    prefix="/api/v1",
    tags=["Predictions"]
)

app.include_router(
    cade.router,
    prefix="/api/v1/cade",
    tags=["CADe (Computer-Aided Detection)"]
)
