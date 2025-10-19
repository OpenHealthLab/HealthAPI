"""
Dependency Injection Container Configuration.

This module defines the DI container that manages all application dependencies
including database sessions, ML models, services, and other components.
"""

from dependency_injector import containers, providers
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.logging_config import get_logger
from app.ml.inference import ModelInference
from app.ml.detection_inference import DetectionInference
from app.ml.preprocessing.image_processor import ImageProcessor
from app.services.prediction_service import PredictionService
from app.services.detection_service import DetectionService
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.role_service import RoleService
from app.services.audit_service import AuditService

class Container(containers.DeclarativeContainer):
    """
    Application-wide dependency injection container.
    
    This container manages the lifecycle of all major components including:
    - Configuration settings
    - Database sessions
    - ML model instances
    - Service layer objects
    - Image processors
    """
    
    # Enable automatic wiring for dependency injection
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.api.routes.predictions",
            "app.api.routes.cade",
            "app.api.routes.health",
            # v2 API modules
            "app.api.v2.auth",
            "app.api.v2.users",
            "app.api.v2.roles",
            "app.api.v2.audit",
        ]
    )
    
    # Configuration
    config = providers.Singleton(get_settings)
    
    # Database
    db = providers.Factory(
        lambda: SessionLocal()
    )
    
    # ML Components
    model_inference = providers.Singleton(ModelInference)
    detection_inference = providers.Singleton(DetectionInference)
    image_processor = providers.Singleton(ImageProcessor)
    
    # Services
    prediction_service = providers.Factory(
        PredictionService
    )
    
    detection_service = providers.Factory(
        DetectionService
    )
    
    auth_service = providers.Factory(
        AuthService
    )
    
    user_service = providers.Factory(
        UserService
    )
    
    role_service = providers.Factory(
        RoleService
    )
    
    audit_service = providers.Factory(
        AuditService
    )
    
    # Logger factory
    logger = providers.Factory(
        get_logger,
        name=providers.Callable(lambda: __name__)
    )
