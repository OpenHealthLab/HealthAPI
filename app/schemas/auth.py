"""
Authentication request/response schemas.

Pydantic models for authentication-related API endpoints.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.core.security import password_hasher


class UserRegister(BaseModel):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    
    @field_validator('username')
    def username_alphanumeric(cls, v):
        """Validate username is alphanumeric with underscores/hyphens."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores and hyphens allowed)')
        return v.lower()
    
    @field_validator('password')
    def password_strength(cls, v):
        """Validate password strength."""
        is_valid, error = password_hasher.validate_password_strength(v)
        if not is_valid:
            raise ValueError(error)
        return v
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "username": "john_doe",
            "email": "john.doe@hospital.com",
            "password": "SecurePass123!",
            "full_name": "Dr. John Doe"
        }
    })


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "username": "john_doe",
            "password": "SecurePass123!"
        }
    })


class UserLogin2FA(BaseModel):
    """Schema for login with 2FA."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    totp_code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "username": "john_doe",
            "password": "SecurePass123!",
            "totp_code": "123456"
        }
    })


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 900
        }
    })


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str = Field(..., description="Refresh token")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
    })


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "current_password": "OldPass123!",
            "new_password": "NewSecurePass456!"
        }
    })


class TwoFactorEnable(BaseModel):
    """Schema for enabling 2FA response."""
    secret: str = Field(..., description="TOTP secret key")
    qr_code: str = Field(..., description="Base64-encoded QR code image")
    backup_codes: Optional[List[str]] = Field(None, description="Backup codes for 2FA")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "secret": "JBSWY3DPEHPK3PXP",
            "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
            "backup_codes": ["12345678", "87654321"]
        }
    })


class TwoFactorVerify(BaseModel):
    """Schema for verifying 2FA setup."""
    totp_code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "totp_code": "123456"
        }
    })


class TwoFactorDisable(BaseModel):
    """Schema for disabling 2FA."""
    password: str = Field(..., description="Current password")
    totp_code: Optional[str] = Field(None, min_length=6, max_length=6, description="Current TOTP code")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "password": "SecurePass123!",
            "totp_code": "123456"
        }
    })


class GoogleAuthRequest(BaseModel):
    """Schema for Google OAuth request."""
    code: str = Field(..., description="Authorization code from Google")
    redirect_uri: str = Field(..., description="Redirect URI used in OAuth flow")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "code": "4/0AY0e-g7...",
            "redirect_uri": "http://localhost:8000/api/v2/auth/google/callback"
        }
    })


class GoogleAuthURL(BaseModel):
    """Schema for Google OAuth URL response."""
    auth_url: str = Field(..., description="Google OAuth authorization URL")
    state: str = Field(..., description="State parameter for CSRF protection")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
            "state": "random_state_string"
        }
    })


class SessionResponse(BaseModel):
    """Schema for session information."""
    id: int
    jti: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    is_valid: bool
    expires_at: datetime
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "jti": "abc123def456",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "is_valid": True,
                "expires_at": "2024-01-15T10:00:00Z",
                "created_at": "2024-01-08T10:00:00Z"
            }
        }
    )


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str = Field(..., description="Response message")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "message": "Operation completed successfully"
        }
    })
