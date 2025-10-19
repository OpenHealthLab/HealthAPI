"""
Role and permission API endpoints (v2).

Provides CRUD operations for roles and management of Casbin permissions.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.user import User
from app.services.role_service import RoleService
from app.services.audit_service import AuditService
from app.core.container import Container
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleListResponse,
    PermissionCreate,
    PermissionCheckRequest,
    PermissionCheckResponse,
)
from app.schemas.auth import MessageResponse
from app.schemas.audit import AuditLogCreate

router = APIRouter()
role_service = Container.role_service()
audit_service = Container.audit_service()

# Authentication dependency imported from shared module
from app.api.dependencies import get_current_user, require_active_user, require_permission

def get_client_info(request: Request) -> tuple:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ip, ua

# ----- Role CRUD -----
@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    role_data: RoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("/api/v2/roles", "POST"))
):
    new_role = role_service.create_role(db, role_data)
    ip, ua = get_client_info(request)
    audit_service.log_action(
        db,
        AuditLogCreate(
            user_id=admin.id,
            action="create_role",
            resource="role",
            resource_id=str(new_role.id),
            status="success",
            ip_address=ip,
            user_agent=ua,
        ),
    )
    return new_role

@router.get("/", response_model=RoleListResponse)
def list_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("/api/v2/roles", "GET"))
):
    roles, total = role_service.list_roles(db, skip, limit)
    return RoleListResponse(roles=roles, total=total)

@router.get("/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("/api/v2/roles/*", "GET"))
):
    role = role_service.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.put("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("/api/v2/roles/*", "PUT"))
):
    updated = role_service.update_role(db, role_id, role_data)
    ip, ua = get_client_info(request)
    audit_service.log_action(
        db,
        AuditLogCreate(
            user_id=admin.id,
            action="update_role",
            resource="role",
            resource_id=str(role_id),
            status="success",
            ip_address=ip,
            user_agent=ua,
        ),
    )
    return updated

@router.delete("/{role_id}", response_model=MessageResponse)
def delete_role(
    role_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("/api/v2/roles/*", "DELETE"))
):
    role_service.delete_role(db, role_id)
    ip, ua = get_client_info(request)
    audit_service.log_action(
        db,
        AuditLogCreate(
            user_id=admin.id,
            action="delete_role",
            resource="role",
            resource_id=str(role_id),
            status="success",
            ip_address=ip,
            user_agent=ua,
        ),
    )
    return MessageResponse(message="Role deleted")

# ----- Permission Management -----
@router.post("/permissions", response_model=MessageResponse)
def add_permission(
    perm: PermissionCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("/api/v2/permissions", "POST"))
):
    role_service.add_permission(perm)
    ip, ua = get_client_info(request)
    audit_service.log_action(
        db,
        AuditLogCreate(
            user_id=admin.id,
            action="add_permission",
            resource="permission",
            status="success",
            details=f"{perm.subject}:{perm.object}:{perm.action}",
            ip_address=ip,
            user_agent=ua,
        ),
    )
    return MessageResponse(message="Permission added")

@router.delete("/permissions", response_model=MessageResponse)
def remove_permission(
    perm: PermissionCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("/api/v2/permissions", "DELETE"))
):
    role_service.remove_permission(perm)
    ip, ua = get_client_info(request)
    audit_service.log_action(
        db,
        AuditLogCreate(
            user_id=admin.id,
            action="remove_permission",
            resource="permission",
            status="success",
            details=f"{perm.subject}:{perm.object}:{perm.action}",
            ip_address=ip,
            user_agent=ua,
        ),
    )
    return MessageResponse(message="Permission removed")

@router.post("/permissions/check", response_model=PermissionCheckResponse)
def check_permission(
    check: PermissionCheckRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_active_user)
):
    allowed = role_service.check_permission(
        user_id=user.id,
        roles=check.roles or [],
        resource=check.resource,
        action=check.action,
    )
    return PermissionCheckResponse(allowed=allowed, reason=None if allowed else "Denied")
