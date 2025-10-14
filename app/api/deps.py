
from fastapi import Header, HTTPException, status
from app.core.config import get_settings

settings = get_settings()

async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key for protected endpoints"""
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return x_api_key

