"""
Audit log schemas.

Pydantic models for audit logging endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class AuditLogBase(BaseModel):
    """Base audit log schema."""
    action: str = Field(..., description="Action performed")
    resource: str = Field(..., description="Resource type")
    resource_id: Optional[str] = Field(None, description="Specific resource ID")
    status: str = Field(..., description="Status: success or failure")
    details: Optional[str] = Field(None, description="Additional details (JSON)")


class AuditLogCreate(AuditLogBase):
    """Schema for creating an audit log entry."""
    user_id: Optional[int] = Field(None, description="User ID (null for anonymous)")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "user_id": 1,
            "action": "login",
            "resource": "auth",
            "resource_id": None,
            "status": "success",
            "details": '{"method": "password"}',
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0..."
        }
    })


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""
    id: int
    user_id: Optional[int]
    username: Optional[str] = Field(None, description="Username of user who performed action")
    action: str
    resource: str
    resource_id: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    status: str
    timestamp: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 1,
                "username": "john_doe",
                "action": "create_prediction",
                "resource": "prediction",
                "resource_id": "123",
                "details": '{"model": "chest_xray_v1", "confidence": 0.95}',
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "status": "success",
                "timestamp": "2024-01-10T09:15:00Z"
            }
        }
    )


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log list."""
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "logs": [
                {
                    "id": 1,
                    "user_id": 1,
                    "username": "john_doe",
                    "action": "login",
                    "resource": "auth",
                    "resource_id": None,
                    "details": None,
                    "ip_address": "192.168.1.1",
                    "user_agent": "Mozilla/5.0...",
                    "status": "success",
                    "timestamp": "2024-01-10T09:15:00Z"
                }
            ],
            "total": 1500,
            "page": 1,
            "page_size": 50
        }
    })


class AuditLogFilter(BaseModel):
    """Schema for filtering audit logs."""
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    action: Optional[str] = Field(None, description="Filter by action")
    resource: Optional[str] = Field(None, description="Filter by resource type")
    status: Optional[str] = Field(None, description="Filter by status")
    start_date: Optional[datetime] = Field(None, description="Start date for date range")
    end_date: Optional[datetime] = Field(None, description="End date for date range")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "user_id": 1,
            "action": "login",
            "resource": "auth",
            "status": "success",
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z"
        }
    })


class AuditLogStats(BaseModel):
    """Schema for audit log statistics."""
    total_logs: int
    successful_actions: int
    failed_actions: int
    unique_users: int
    actions_by_type: dict = Field(..., description="Count of actions by type")
    recent_failures: List[AuditLogResponse] = Field(..., description="Recent failed actions")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total_logs": 10000,
            "successful_actions": 9750,
            "failed_actions": 250,
            "unique_users": 45,
            "actions_by_type": {
                "login": 1500,
                "create_prediction": 5000,
                "view_prediction": 3000,
                "logout": 500
            },
            "recent_failures": [
                {
                    "id": 9999,
                    "user_id": 5,
                    "username": "jane_smith",
                    "action": "login",
                    "resource": "auth",
                    "resource_id": None,
                    "details": "{\"error\": \"Invalid password\"}",
                    "ip_address": "192.168.1.5",
                    "user_agent": "Mozilla/5.0...",
                    "status": "failure",
                    "timestamp": "2024-01-10T10:30:00Z"
                }
            ]
        }
    })
