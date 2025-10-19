"""
Audit log API endpoints (v2).

Provides admin access to audit logs, statistics, and CSV export.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.audit_service import AuditService
from app.schemas.audit import (
    AuditLogCreate,
    AuditLogFilter,
    AuditLogStats,
    AuditLogListResponse,
)
from app.schemas.auth import MessageResponse

router = APIRouter()
audit_service = AuditService()

def get_current_user():
    """Placeholder for authentication dependency (Phase 5)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication middleware not yet implemented"
    )

def get_client_info(request: Request) -> tuple:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ip, ua

@router.get("/", response_model=AuditLogListResponse)
def list_audit_logs(
    skip: int = 0,
    limit: int = 50,
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    resource: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    admin = Depends(get_current_user)  # placeholder
):
    """
    List audit logs with optional filtering (admin only).
    """
    filter_params = AuditLogFilter(
        user_id=user_id,
        action=action,
        resource=resource,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )
    logs, total = audit_service.get_logs(db, skip, limit, filter_params)
    return AuditLogListResponse(
        logs=logs,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )

@router.get("/me", response_model=AuditLogListResponse)
def my_audit_logs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)  # placeholder
):
    """
    Retrieve audit logs for the currently authenticated user.
    """
    logs, total = audit_service.get_user_logs(db, user.id, skip, limit)
    return AuditLogListResponse(
        logs=logs,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )

@router.get("/stats", response_model=AuditLogStats)
def get_stats(
    db: Session = Depends(get_db),
    admin = Depends(get_current_user)  # placeholder
):
    """
    Return aggregated audit log statistics (admin only).
    """
    return audit_service.get_stats(db)

@router.get("/export", response_model=MessageResponse)
def export_logs(
    db: Session = Depends(get_db),
    admin = Depends(get_current_user)  # placeholder
):
    """
    Export audit logs as CSV (admin only).

    In a full implementation this would return a StreamingResponse.
    Here we return a placeholder message.
    """
    csv_data = audit_service.export_logs_csv(db)
    # Placeholder: in production you would stream `csv_data` back to the client.
    return MessageResponse(message="CSV export generated (placeholder)")
    """
    Export audit logs as CSV (admin only).

    In a full implementation this would return a StreamingResponse.
    Here we return a placeholder message.
    """
    csv_data = audit_service.export_logs_csv(db)
    # Placeholder: in production you would stream `csv_data` back to the client.
    return MessageResponse(message="CSV export generated (placeholder)")
