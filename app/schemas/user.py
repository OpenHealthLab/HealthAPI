"""
User management schemas.

Pydantic models for user-related API endpoints.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.core.security import password_hasher


class UserBase(BaseModel):
    """Base user schema with common fields."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a user (admin only)."""
    password: str = Field(..., min_length=8)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    roles: Optional[List[str]] = Field(default=[], description="List of role names to assign")
    
    @field_validator('password')
    def password_strength(cls, v):
        """Validate password strength."""
        is_valid, error = password_hasher.validate_password_strength(v)
        if not is_valid:
            raise ValueError(error)
        return v
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "username": "jane_smith",
            "email": "jane.smith@hospital.com",
            "password": "SecurePass123!",
            "full_name": "Dr. Jane Smith",
            "is_active": True,
            "is_superuser": False,
            "roles": ["doctor", "researcher"]
        }
    })


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "email": "new.email@hospital.com",
            "full_name": "Dr. Jane Smith, MD",
            "is_active": True
        }
    })


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    oauth_provider: Optional[str]
    is_2fa_enabled: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime]
    roles: List[str] = Field(default=[], description="List of assigned role names")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "john_doe",
                "email": "john.doe@hospital.com",
                "full_name": "John Doe",
                "is_active": True,
                "is_superuser": False,
                "oauth_provider": None,
                "is_2fa_enabled": True,
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-08T15:30:00Z",
                "last_login": "2024-01-10T09:15:00Z",
                "roles": ["doctor", "researcher"]
            }
        }
    )


class UserListResponse(BaseModel):
    """Schema for paginated user list."""
    total: int = Field(..., description="Total number of users")
    users: List[UserResponse] = Field(..., description="List of users")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total": 50,
            "users": [
                {
                    "id": 1,
                    "username": "john_doe",
                    "email": "john.doe@hospital.com",
                    "full_name": "John Doe",
                    "is_active": True,
                    "is_superuser": False,
                    "oauth_provider": None,
                    "is_2fa_enabled": True,
                    "created_at": "2024-01-01T10:00:00Z",
                    "updated_at": None,
                    "last_login": "2024-01-10T09:15:00Z",
                    "roles": ["doctor"]
                }
            ],
            "page": 1,
            "page_size": 10
        }
    })


class UserProfileUpdate(BaseModel):
    """Schema for users updating their own profile."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "email": "new.email@hospital.com",
            "full_name": "Dr. John Doe, MD, PhD"
        }
    })


class RoleAssignment(BaseModel):
    """Schema for assigning/removing roles."""
    role_name: str = Field(..., description="Role name to assign/remove")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "role_name": "radiologist"
        }
    })


class UserStats(BaseModel):
    """Schema for user statistics (admin)."""
    total_users: int
    active_users: int
    inactive_users: int
    users_with_2fa: int
    oauth_users: int
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total_users": 150,
            "active_users": 142,
            "inactive_users": 8,
            "users_with_2fa": 95,
            "oauth_users": 30
        }
    })
