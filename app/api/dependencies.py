"""
Common FastAPI dependencies for authentication, RBAC, and rate limiting.

Provides:
- `get_current_user` – validates JWT access token, loads user from DB,
  and attaches Casbin role information.
- `require_active_user` – ensures the user is active.
- `rate_limiter` – SlowAPI rate limiting dependency.
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import token_manager, password_hasher
from app.core.database import get_db
from app.models.user import User, UserRole, Role
from app.services.role_service import RoleService
from app.core.casbin_enforcer import casbin_enforcer
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Rate limiting
# ----------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

def rate_limiter():
    """Dependency that can be added to any route to enable rate limiting."""
    return limiter

# ----------------------------------------------------------------------
# Authentication & RBAC
# ----------------------------------------------------------------------
security = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Validate JWT access token, load the user and attach role information.

    Returns the `User` ORM instance.
    Raises 401 if token is missing/invalid or user not found.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )
    token = credentials.credentials
    payload = token_manager.verify_token(token, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    # Load roles for Casbin checks
    # user.roles is already a list of role name strings from the @property
    user._casbin_roles = user.roles  # attach for later use
    return user

def require_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensures the authenticated user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return current_user

def check_permission(
    user: User,
    resource: str,
    action: str,
) -> bool:
    """
    Helper to check Casbin permission for the current user.
    """
    roles = getattr(user, "_casbin_roles", [])
    return casbin_enforcer.check_permission(
        user_id=user.id,
        roles=roles,
        resource=resource,
        action=action,
    )

def require_permission(resource: str, action: str):
    """
    Dependency factory that creates a dependency to check permissions.
    
    Usage:
        @router.post("/roles/")
        def create_role(
            ...,
            user: User = Depends(require_permission("/api/v2/roles", "POST"))
        ):
            ...
    """
    def permission_checker(
        request: Request,
        current_user: User = Depends(require_active_user)
    ) -> User:
        if not check_permission(current_user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions to {action} {resource}",
            )
        return current_user
    return permission_checker
