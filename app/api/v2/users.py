"""
User management API endpoints (v2).

Provides routes for:
- Current user profile retrieval & update
- Password change
- Admin user CRUD operations
- Role assignment/removal
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.user_service import UserService
from app.services.audit_service import AuditService
from app.core.container import Container
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    RoleAssignment,
)
from app.schemas.auth import PasswordChange, MessageResponse
from app.schemas.audit import AuditLogCreate

router = APIRouter()
user_service = Container.user_service()
audit_service = Container.audit_service()

# Placeholder for authentication dependency (to be implemented in Phase 5)
# Authentication dependency imported from shared module
from app.api.dependencies import get_current_user, require_active_user

def get_client_info(request: Request) -> tuple:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ip, ua

@router.get("/me", response_model=UserResponse)
def read_current_user(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Return the profile of the authenticated user."""
    return user_service.get_user_by_id(db, current_user.id)

@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update profile of the authenticated user."""
    updated = user_service.update_user(db, current_user.id, user_data)
    ip, ua = get_client_info(request)
    audit_service.log_action(
        db,
        AuditLogCreate(
            user_id=current_user.id,
            action="update_profile",
            resource="user",
            resource_id=str(current_user.id),
            status="success",
            ip_address=ip,
            user_agent=ua,
        ),
    )
    return updated

@router.post("/me/change-password", response_model=MessageResponse)
def change_password(
    pwd: PasswordChange,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Change password for the authenticated user."""
    user_service.change_password(
        db, current_user.id, pwd.current_password, pwd.new_password
    )
    ip, ua = get_client_info(request)
    audit_service.log_action(
        db,
        AuditLogCreate(
            user_id=current_user.id,
            action="change_password",
            resource="user",
            resource_id=str(current_user.id),
            status="success",
            ip_address=ip,
            user_agent=ua,
        ),
    )
    return MessageResponse(message="Password changed successfully")

# ----- Admin routes -----
@router.get("/", response_model=UserListResponse)
def list_users(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    db: Session = Depends(get_db),
    admin = Depends(get_current_user)  # placeholder
):
    """List users (admin)."""
    users, total = user_service.list_users(db, skip, limit, is_active)
    return UserListResponse(total=total, users=users, page=skip // limit + 1, page_size=limit)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin = Depends(get_current_user)  # placeholder
):
    """Create a new user (admin)."""
    new_user = user_service.create_user(db, user_data, created_by=admin.id)
    ip, ua = get_client_info(request)
    audit_service.log_action(
        db,
        AuditLogCreate(
            user_id=admin.id,
            action="create_user",
            resource="user",
            resource_id=str(new_user.id),
            status="success",
            ip_address=ip,
            user_agent=ua,
        ),
    )
    return new_user

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_user)  # placeholder
):
    """Get user by ID (admin)."""
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin = Depends(get_current_user)  # placeholder
):
    """Update user (admin)."""
    updated = user_service.update_user(db, user_id, user_data)
    ip, ua = get_client_info(request)
    audit_service.log_action(
        db,
        AuditLogCreate(
            user_id=admin.id,
            action="update_user",
            resource="user",
            resource_id=str(user_id),
            status="success",
            ip_address=ip,
            user_agent=ua,
        ),
    )
    return updated

@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin = Depends(get_current_user)  # placeholder
):
    """Delete user (admin)."""
    user_service.delete_user(db, user_id)
    ip, ua = get_client_info(request)
    audit_service.log_action(
        db,
        AuditLogCreate(
            user_id=admin.id,
            action="delete_user",
            resource="user",
            resource_id=str(user_id),
            status="success",
            ip_address=ip,
            user_agent=ua,
        ),
    )
    return MessageResponse(message="User deleted")

@router.post("/{user_id}/roles", response_model=MessageResponse)
def assign_role(
    user_id: int,
    role: RoleAssignment,
    request: Request,
    db: Session = Depends(get_db),
    admin = Depends(get_current_user)  # placeholder
):
    """Assign a role to a user (admin)."""
    user_service.assign_role(db, user_id, role.role_name, assigned_by=admin.id)
    ip, ua = get_client_info(request)
    audit_service.log_action(
        db,
        AuditLogCreate(
            user_id=admin.id,
            action="assign_role",
            resource="user",
            resource_id=str(user_id),
            status="success",
            details=f"Role {role.role_name}",
            ip_address=ip,
            user_agent=ua,
        ),
    )
    return MessageResponse(message="Role assigned")

@router.delete("/{user_id}/roles/{role_name}", response_model=MessageResponse)
def remove_role(
    user_id: int,
    role_name: str,
    request: Request,
    db: Session = Depends(get_db),
    admin = Depends(get_current_user)  # placeholder
):
    """Remove a role from a user (admin)."""
    user_service.remove_role(db, user_id, role_name)
    ip, ua = get_client_info(request)
    audit_service.log_action(
        db,
        AuditLogCreate(
            user_id=admin.id,
            action="remove_role",
            resource="user",
            resource_id=str(user_id),
            status="success",
            details=f"Role {role_name}",
            ip_address=ip,
            user_agent=ua,
        ),
    )
    return MessageResponse(message="Role removed")
