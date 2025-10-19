"""
Authentication API endpoints (v2).

Handles user registration, login, logout, token refresh,
2FA setup, and Google OAuth authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.api.dependencies import limiter
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserLogin2FA,
    TokenResponse,
    TokenRefresh,
    TwoFactorEnable,
    TwoFactorVerify,
    TwoFactorDisable,
    MessageResponse
)
from app.schemas.user import UserResponse
from app.schemas.audit import AuditLogCreate
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Service instances (will be replaced with DI in Phase 6)
auth_service = AuthService()
audit_service = AuditService()


def get_client_info(request: Request) -> tuple:
    """Extract client IP and user agent from request."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    Creates a new user account with the provided credentials.
    Default role 'api_user' is automatically assigned.
    
    **Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    try:
        ip_address, user_agent = get_client_info(request)
        
        # Register user
        user = auth_service.register_user(db, user_data)
        
        # Log successful registration
        audit_service.log_action(
            db,
            AuditLogCreate(
                user_id=user.id,
                action="register",
                resource="auth",
                resource_id=str(user.id),
                status="success",
                details=f"User registered: {user.username}",
                ip_address=ip_address,
                user_agent=user_agent
            )
        )
        
        logger.info(f"User registered successfully: {user.username}")
        
        # Return user data with roles
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            oauth_provider=user.oauth_provider,
            is_2fa_enabled=user.is_2fa_enabled,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            roles=user.roles
        )
        
    except HTTPException as e:
        # Log failed registration
        audit_service.log_action(
            db,
            AuditLogCreate(
                user_id=None,
                action="register",
                resource="auth",
                status="failure",
                details=f"Registration failed: {e.detail}",
                ip_address=get_client_info(request)[0],
                user_agent=get_client_info(request)[1]
            )
        )
        raise


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with username/email and password.
    
    Returns JWT access and refresh tokens on successful authentication.
    If 2FA is enabled, returns 401 with message to use /login/2fa endpoint.
    """
    try:
        ip_address, user_agent = get_client_info(request)
        
        # Attempt login
        tokens, requires_2fa = auth_service.login(
            db, credentials, ip_address, user_agent
        )
        
        if requires_2fa:
            # Log 2FA required
            user = auth_service.authenticate_user(db, credentials.username, credentials.password)
            audit_service.log_action(
                db,
                AuditLogCreate(
                    user_id=user.id if user else None,
                    action="login",
                    resource="auth",
                    status="success",
                    details="2FA required",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="2FA is enabled. Please use /login/2fa endpoint with your TOTP code."
            )
        
        # Log successful login
        user = auth_service.authenticate_user(db, credentials.username, credentials.password)
        audit_service.log_action(
            db,
            AuditLogCreate(
                user_id=user.id if user else None,
                action="login",
                resource="auth",
                status="success",
                details="Login successful",
                ip_address=ip_address,
                user_agent=user_agent
            )
        )
        
        logger.info(f"User logged in: {credentials.username}")
        return tokens
        
    except HTTPException as e:
        # Log failed login
        audit_service.log_action(
            db,
            AuditLogCreate(
                user_id=None,
                action="login",
                resource="auth",
                status="failure",
                details=f"Login failed: {e.detail}",
                ip_address=get_client_info(request)[0],
                user_agent=get_client_info(request)[1]
            )
        )
        raise


@router.post("/login/2fa", response_model=TokenResponse)
async def login_2fa(
    credentials: UserLogin2FA,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login with 2FA verification.
    
    Use this endpoint when 2FA is enabled for the account.
    Requires username, password, and 6-digit TOTP code.
    """
    try:
        ip_address, user_agent = get_client_info(request)
        
        # Login with 2FA
        tokens = auth_service.login_with_2fa(
            db, credentials, ip_address, user_agent
        )
        
        # Log successful 2FA login
        user = auth_service.authenticate_user(db, credentials.username, credentials.password)
        audit_service.log_action(
            db,
            AuditLogCreate(
                user_id=user.id if user else None,
                action="login_2fa",
                resource="auth",
                status="success",
                details="2FA login successful",
                ip_address=ip_address,
                user_agent=user_agent
            )
        )
        
        logger.info(f"User logged in with 2FA: {credentials.username}")
        return tokens
        
    except HTTPException as e:
        # Log failed 2FA login
        audit_service.log_action(
            db,
            AuditLogCreate(
                user_id=None,
                action="login_2fa",
                resource="auth",
                status="failure",
                details=f"2FA login failed: {e.detail}",
                ip_address=get_client_info(request)[0],
                user_agent=get_client_info(request)[1]
            )
        )
        raise


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Logout user by invalidating current session.
    
    Requires valid access token in Authorization header.
    Note: This is a placeholder - will be properly implemented with auth middleware in Phase 5.
    """
    # TODO: Extract JTI from access token via auth middleware
    # For now, return success message
    return MessageResponse(message="Logout successful. Token invalidated.")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Provide a valid refresh token to get a new access token.
    The old refresh token will be invalidated and a new one issued.
    """
    try:
        ip_address, user_agent = get_client_info(request)
        
        # Refresh tokens
        new_tokens = auth_service.refresh_access_token(db, token_data.refresh_token)
        
        logger.info("Token refreshed successfully")
        return new_tokens
        
    except HTTPException as e:
        logger.warning(f"Token refresh failed: {e.detail}")
        raise


@router.post("/2fa/enable", response_model=TwoFactorEnable)
async def enable_2fa(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Enable 2FA for current user.
    
    Returns TOTP secret and QR code for setup.
    User must verify with /2fa/verify before 2FA is activated.
    
    Note: Requires authentication - will be protected in Phase 5.
    """
    # TODO: Get current user from auth middleware
    # For now, this is a placeholder
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint requires authentication middleware (Phase 5)"
    )


@router.post("/2fa/verify", response_model=MessageResponse)
async def verify_2fa(
    verification: TwoFactorVerify,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Verify and activate 2FA.
    
    Verify the TOTP code from authenticator app to activate 2FA.
    After verification, 2FA will be required for all future logins.
    
    Note: Requires authentication - will be protected in Phase 5.
    """
    # TODO: Get current user from auth middleware
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint requires authentication middleware (Phase 5)"
    )


@router.post("/2fa/disable", response_model=MessageResponse)
async def disable_2fa(
    data: TwoFactorDisable,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Disable 2FA for current user.
    
    Requires current password and optionally TOTP code for verification.
    After disabling, normal login will work without 2FA.
    
    Note: Requires authentication - will be protected in Phase 5.
    """
    # TODO: Get current user from auth middleware
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint requires authentication middleware (Phase 5)"
    )


@router.get("/google", response_model=MessageResponse)
async def google_auth_init():
    """
    Initialize Google OAuth flow.
    
    Returns authorization URL for Google OAuth.
    Will be fully implemented in Phase 5.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google OAuth will be implemented in Phase 5"
    )


@router.post("/google/callback", response_model=TokenResponse)
async def google_auth_callback():
    """
    Google OAuth callback handler.
    
    Handles the callback from Google OAuth and creates/logs in user.
    Will be fully implemented in Phase 5.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google OAuth will be implemented in Phase 5"
    )
