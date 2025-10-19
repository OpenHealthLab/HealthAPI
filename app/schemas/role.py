"""
Role management schemas.

Pydantic models for role-related API endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class RoleBase(BaseModel):
    """Base role schema."""
    name: str = Field(..., min_length=2, max_length=50, description="Role name (lowercase)")
    display_name: str = Field(..., max_length=100, description="Human-readable role name")
    description: Optional[str] = Field(None, max_length=500, description="Role description")


class RoleCreate(RoleBase):
    """Schema for creating a role."""
    is_system_role: bool = Field(default=False, description="Whether this is a protected system role")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "nurse",
            "display_name": "Nurse",
            "description": "Nursing staff with basic access to patient records",
            "is_system_role": False
        }
    })


class RoleUpdate(BaseModel):
    """Schema for updating a role."""
    display_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "display_name": "Senior Nurse",
            "description": "Senior nursing staff with extended access"
        }
    })


class RoleResponse(BaseModel):
    """Schema for role response."""
    id: int
    name: str
    display_name: str
    description: Optional[str]
    is_system_role: bool
    created_at: datetime
    user_count: int = Field(default=0, description="Number of users with this role")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "doctor",
                "display_name": "Doctor",
                "description": "Medical doctor with full access to patient records",
                "is_system_role": True,
                "created_at": "2024-01-01T10:00:00Z",
                "user_count": 45
            }
        }
    )


class RoleListResponse(BaseModel):
    """Schema for role list."""
    roles: List[RoleResponse]
    total: int
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "roles": [
                {
                    "id": 1,
                    "name": "doctor",
                    "display_name": "Doctor",
                    "description": "Medical doctor",
                    "is_system_role": True,
                    "created_at": "2024-01-01T10:00:00Z",
                    "user_count": 45
                }
            ],
            "total": 7
        }
    })


class PermissionCreate(BaseModel):
    """Schema for creating a permission/policy."""
    subject: str = Field(..., description="Role or user identifier")
    object: str = Field(..., description="Resource path (e.g., /api/v1/predict)")
    action: str = Field(..., description="HTTP method or action (e.g., GET, POST, *)")
    effect: str = Field(default="allow", description="Effect: 'allow' or 'deny'")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "subject": "nurse",
            "object": "/api/v1/predictions",
            "action": "GET",
            "effect": "allow"
        }
    })


class PermissionResponse(BaseModel):
    """Schema for permission/policy response."""
    subject: str
    object: str
    action: str
    effect: str
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "subject": "doctor",
            "object": "/api/v1/predict",
            "action": "POST",
            "effect": "allow"
        }
    })


class PermissionListResponse(BaseModel):
    """Schema for permissions list."""
    permissions: List[PermissionResponse]
    total: int
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "permissions": [
                {
                    "subject": "doctor",
                    "object": "/api/v1/predict",
                    "action": "POST",
                    "effect": "allow"
                }
            ],
            "total": 25
        }
    })


class PermissionCheckRequest(BaseModel):
    """Schema for checking permissions."""
    user_id: Optional[int] = Field(None, description="User ID (if checking for specific user)")
    roles: Optional[List[str]] = Field(None, description="Roles to check")
    resource: str = Field(..., description="Resource path")
    action: str = Field(..., description="HTTP method")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "user_id": 1,
            "roles": ["doctor"],
            "resource": "/api/v1/predict",
            "action": "POST"
        }
    })


class PermissionCheckResponse(BaseModel):
    """Schema for permission check result."""
    allowed: bool = Field(..., description="Whether permission is granted")
    reason: Optional[str] = Field(None, description="Reason for decision")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "allowed": True,
            "reason": "User has 'doctor' role with required permission"
        }
    })
