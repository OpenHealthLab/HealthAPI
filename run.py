"""
Application entry point.

This script starts the FastAPI application using Uvicorn server
with settings loaded from the configuration.

Usage:
    python run.py
    
For development with auto-reload:
    Set DEBUG=True in .env file
    
For production:
    Set DEBUG=False and use a production ASGI server like Gunicorn
"""

import uvicorn
from app.core.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Debug mode: {settings.debug}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
