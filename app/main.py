
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import engine, Base
from app.api.routes import health, predictions
from app.ml.inference import ModelInference

settings = get_settings()
model_inference = ModelInference()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("Starting Healthcare AI Backend...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created")
    
    # Load ML model
    try:
        model_inference.load_model()
        print("ML model loaded successfully")
    except Exception as e:
        print(f"Warning: Could not load ML model: {e}")
    
    yield
    
    # Shutdown
    print("Shutting down Healthcare AI Backend...")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="REST API for Healthcare AI Models - Chest X-Ray Analysis",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(
    predictions.router,
    prefix="/api/v1",
    tags=["Predictions"]
)

