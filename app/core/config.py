"""
Application configuration management.

This module handles all configuration settings using Pydantic Settings,
which automatically loads values from environment variables and .env files.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden by setting environment variables
    or by creating a .env file in the project root.
    
    Attributes:
        app_name: Name of the application
        app_version: Current version of the application
        debug: Enable debug mode (verbose logging, auto-reload)
        host: Host address to bind the server
        port: Port number to bind the server
        database_url: Database connection string
        model_path: Path to the trained PyTorch model file
        upload_dir: Directory for storing uploaded images
        max_upload_size: Maximum file upload size in bytes
        api_key: API key for authentication (change in production!)
    """
    
    # Application Settings
    app_name: str = "Healthcare AI Backend"
    app_version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database Configuration
    database_url: str = "sqlite:///./healthcare_ai.db"
    
    # Model Configuration
    model_path: str = "./ml_models/chest_xray_model.pth"
    upload_dir: str = "./uploads"
    max_upload_size: int = 10485760  # 10MB in bytes
    
    # Security
    api_key: str = "your-secret-api-key"
    
    # Optional Settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    This function uses lru_cache to ensure settings are only loaded once
    and reused throughout the application lifecycle.
    
    Returns:
        Settings: Application configuration object
        
    Example:
        >>> settings = get_settings()
        >>> print(settings.app_name)
        Healthcare AI Backend
    """
    return Settings()
