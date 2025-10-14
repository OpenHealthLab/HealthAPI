"""
API dependencies for FastAPI endpoints.

This module contains dependency functions used across API routes,
such as authentication and authorization.
"""

from fastapi import Header, HTTPException, status
from app.core.config import get_settings

settings = get_settings()


async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """
    Verify API key for protected endpoints.
    
    This dependency can be used to protect endpoints that require
    authentication. The API key should be passed in the X-API-Key header.
    
    Args:
        x_api_key: API key from request header
        
    Returns:
        str: The validated API key
        
    Raises:
        HTTPException: If API key is invalid (401 Unauthorized)
        
    Example:
        >>> from fastapi import Depends
        >>> @app.get("/protected")
        >>> async def protected_route(api_key: str = Depends(verify_api_key)):
        >>>     return {"message": "Access granted"}
        
    Usage in requests:
        >>> import requests
        >>> headers = {"X-API-Key": "your-secret-api-key"}
        >>> response = requests.get("http://localhost:8000/protected", headers=headers)
    """
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return x_api_key
