"""
Main FastAPI application module.

Includes v2 API routers, rate‑limiting middleware, DI container wiring,
and startup tasks for DB, model loading, role seeding, and Casbin initialization.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import engine, Base
from app.core.logging_config import LoggerSetup, get_logger
from app.core.container import Container
from app.core.casbin_enforcer import casbin_enforcer

# Import routers
from app.api.routes import health, predictions, cade
from app.api.v2 import auth as auth_v2, users as users_v2, roles as roles_v2, audit as audit_v2

# Rate limiting
from app.api.dependencies import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

settings = get_settings()

# Initialize logging system
LoggerSetup.setup_logging(
    log_level=settings.log_level,
    log_file=settings.log_file,
    log_dir="logs"
)
logger = get_logger(__name__)

# Initialize DI container
container = Container()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
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

    # Seed initial roles and policies if they do not exist
    try:
        db = container.db()
        role_service = container.role_service()
        from app.schemas.role import RoleCreate
        essential_roles = [
            {"name": "api_user", "display_name": "API User", "description": "Default API user role", "is_system_role": False},
            {"name": "admin", "display_name": "Administrator", "description": "Full access admin role", "is_system_role": True},
            {"name": "doctor", "display_name": "Doctor", "description": "Medical doctor role", "is_system_role": False},
            {"name": "radiologist", "display_name": "Radiologist", "description": "Radiology specialist", "is_system_role": False},
        ]
        for role_data in essential_roles:
            existing = db.query(role_service._service_model).filter_by(name=role_data["name"]).first()
            if not existing:
                role_service.create_role(db, RoleCreate(**role_data))
                logger.info(f"Created initial role: {role_data['name']}")
        db.commit()
    except Exception as e:
        logger.warning(f"Role seeding failed or already completed: {e}")

    # Initialize Casbin enforcer (load model and policies)
    try:
        casbin_enforcer.initialize()
        logger.info("✓ Casbin enforcer initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Casbin enforcer: {e}")

    # Load ML models from DI container
    try:
        model_inference = container.model_inference()
        model_inference.load_model()
        logger.info("✓ Classification model loaded successfully")
    except Exception as e:
        logger.warning(f"Could not load classification model: {e}")

    try:
        detection_inference = container.detection_inference()
        detection_inference.load_model()
        logger.info("✓ Detection model loaded successfully")
    except Exception as e:
        logger.warning(f"Could not load detection model: {e}")

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include API routers
app.include_router(health.router, tags=["Health"])
app.include_router(predictions.router, prefix="/api/v1", tags=["Predictions"])
app.include_router(cade.router, prefix="/api/v1/cade", tags=["CADe"])

# v2 routers (protected by middleware & dependencies)
app.include_router(auth_v2.router, prefix="/api/v2/auth", tags=["Auth v2"])
app.include_router(users_v2.router, prefix="/api/v2/users", tags=["Users v2"])
app.include_router(roles_v2.router, prefix="/api/v2/roles", tags=["Roles v2"])
app.include_router(audit_v2.router, prefix="/api/v2/audit", tags=["Audit v2"])

# Wire the container to the modules (including v2)
container.wire(modules=[
    "app.api.routes.predictions",
    "app.api.routes.cade",
    "app.api.routes.health",
    "app.api.v2.auth",
    "app.api.v2.users",
    "app.api.v2.roles",
    "app.api.v2.audit",
])
