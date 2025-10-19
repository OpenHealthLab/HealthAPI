"""
Authentication service for user registration, login, and token management.

This service handles all authentication-related business logic including
registration, login (with optional 2FA), token management, and OAuth.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, Role, UserRole, Session as SessionModel
from app.schemas.auth import UserRegister, UserLogin, UserLogin2FA, TokenResponse
from app.core.security import password_hasher, token_manager, totp_manager
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AuthService:
    """
    Authentication service for user registration and login.
    
    Handles user registration, authentication, token generation,
    and 2FA operations.
    """
    
    def register_user(
        self,
        db: Session,
        user_data: UserRegister,
        default_role: str = "api_user"
    ) -> User:
        """
        Register a new user.
        
        Args:
            db: Database session
            user_data: User registration data
            default_role: Default role to assign (default: 'api_user')
            
        Returns:
            Created user object
            
        Raises:
            HTTPException: If username or email already exists
        """
        # Check if username exists
        existing_user = db.query(User).filter(
            User.username == user_data.username.lower()
        ).first()
        
        if existing_user:
            logger.warning(f"Registration failed: Username '{user_data.username}' already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email exists
        existing_email = db.query(User).filter(
            User.email == user_data.email
        ).first()
        
        if existing_email:
            logger.warning(f"Registration failed: Email '{user_data.email}' already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate password strength
        is_valid, error_msg = password_hasher.validate_password_strength(user_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Hash password
        hashed_password = password_hasher.hash_password(user_data.password)
        
        # Create user
        new_user = User(
            username=user_data.username.lower(),
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            is_active=True,
            oauth_provider="local"
        )
        
        db.add(new_user)
        db.flush()  # Get user ID
        
        # Assign default role
        role = db.query(Role).filter(Role.name == default_role).first()
        if role:
            user_role = UserRole(
                user_id=new_user.id,
                role_id=role.id,
                assigned_by=None  # Self-registration
            )
            db.add(user_role)
        else:
            logger.warning(f"Default role '{default_role}' not found")
        
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"User registered successfully: {new_user.username} (ID: {new_user.id})")
        return new_user
    
    def authenticate_user(
        self,
        db: Session,
        username: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate user with username/email and password.
        
        Args:
            db: Database session
            username: Username or email
            password: Password
            
        Returns:
            User object if authenticated, None otherwise
        """
        # Try to find user by username or email
        user = db.query(User).filter(
            (User.username == username.lower()) | (User.email == username)
        ).first()
        
        if not user:
            logger.warning(f"Authentication failed: User '{username}' not found")
            return None
        
        if not user.hashed_password:
            logger.warning(f"Authentication failed: User '{username}' has no password (OAuth user)")
            return None
        
        # Verify password
        if not password_hasher.verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: Invalid password for user '{username}'")
            return None
        
        if not user.is_active:
            logger.warning(f"Authentication failed: User '{username}' is inactive")
            return None
        
        logger.info(f"User authenticated successfully: {user.username}")
        return user
    
    def create_user_tokens(
        self,
        db: Session,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TokenResponse:
        """
        Create access and refresh tokens for user.
        
        Args:
            db: Database session
            user: User object
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            TokenResponse with access and refresh tokens
        """
        # Get user roles (user.roles property already returns list of role names)
        roles = user.roles
        
        # Create token data
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "roles": roles
        }
        
        # Create tokens
        access_token = token_manager.create_access_token(token_data)
        refresh_token = token_manager.create_refresh_token(token_data)
        
        # Decode to get JTI
        access_payload = token_manager.decode_token(access_token)
        refresh_payload = token_manager.decode_token(refresh_token)
        
        # Store session
        session = SessionModel(
            user_id=user.id,
            jti=access_payload["jti"],
            refresh_token=token_manager.hash_token(refresh_token),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc),
            is_valid=True
        )
        
        db.add(session)
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        
        db.commit()
        
        logger.info(f"Tokens created for user: {user.username}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=15 * 60  # 15 minutes in seconds
        )
    
    def login(
        self,
        db: Session,
        credentials: UserLogin,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[TokenResponse, bool]:
        """
        Login user with username and password.
        
        Args:
            db: Database session
            credentials: Login credentials
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Tuple of (TokenResponse, requires_2fa)
            
        Raises:
            HTTPException: If authentication fails
        """
        user = self.authenticate_user(db, credentials.username, credentials.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Check if 2FA is enabled
        if user.is_2fa_enabled and user.totp_secret:
            logger.info(f"2FA required for user: {user.username}")
            return None, True
        
        # Create tokens
        tokens = self.create_user_tokens(db, user, ip_address, user_agent)
        return tokens, False
    
    def login_with_2fa(
        self,
        db: Session,
        credentials: UserLogin2FA,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TokenResponse:
        """
        Login user with 2FA verification.
        
        Args:
            db: Database session
            credentials: Login credentials with TOTP code
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            TokenResponse
            
        Raises:
            HTTPException: If authentication fails
        """
        user = self.authenticate_user(db, credentials.username, credentials.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not user.is_2fa_enabled or not user.totp_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA not enabled for this user"
            )
        
        # Verify TOTP code
        if not totp_manager.verify_totp(user.totp_secret, credentials.totp_code):
            logger.warning(f"Invalid 2FA code for user: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code"
            )
        
        logger.info(f"2FA verification successful for user: {user.username}")
        
        # Create tokens
        return self.create_user_tokens(db, user, ip_address, user_agent)
    
    def logout(self, db: Session, jti: str) -> bool:
        """
        Logout user by invalidating session.
        
        Args:
            db: Database session
            jti: JWT ID from access token
            
        Returns:
            True if session invalidated, False otherwise
        """
        session = db.query(SessionModel).filter(
            SessionModel.jti == jti,
            SessionModel.is_valid == True
        ).first()
        
        if session:
            session.is_valid = False
            db.commit()
            logger.info(f"Session invalidated for JTI: {jti}")
            return True
        
        return False
    
    def refresh_access_token(
        self,
        db: Session,
        refresh_token: str
    ) -> TokenResponse:
        """
        Create new access token from refresh token.
        
        Args:
            db: Database session
            refresh_token: Refresh token
            
        Returns:
            New TokenResponse
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        # Verify refresh token
        payload = token_manager.verify_token(refresh_token, token_type="refresh")
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if session is valid
        token_hash = token_manager.hash_token(refresh_token)
        session = db.query(SessionModel).filter(
            SessionModel.refresh_token == token_hash,
            SessionModel.is_valid == True
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session not found or expired"
            )
        
        # Get user
        user_id = int(payload["sub"])
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Invalidate old session
        session.is_valid = False
        db.commit()
        
        # Create new tokens
        return self.create_user_tokens(db, user, session.ip_address, session.user_agent)
    
    def enable_2fa(self, db: Session, user: User) -> Dict[str, str]:
        """
        Enable 2FA for user and generate QR code.
        
        Args:
            db: Database session
            user: User object
            
        Returns:
            Dict with secret and QR code
        """
        # Generate TOTP secret
        secret = totp_manager.generate_secret()
        
        # Generate QR code
        qr_code = totp_manager.generate_qr_code(
            secret=secret,
            username=user.email,
            issuer="HealthAPI"
        )
        
        # Store secret (not yet enabled)
        user.totp_secret = secret
        db.commit()
        
        logger.info(f"2FA secret generated for user: {user.username}")
        
        return {
            "secret": secret,
            "qr_code": qr_code
        }
    
    def verify_and_enable_2fa(
        self,
        db: Session,
        user: User,
        totp_code: str
    ) -> bool:
        """
        Verify TOTP code and enable 2FA.
        
        Args:
            db: Database session
            user: User object
            totp_code: 6-digit TOTP code
            
        Returns:
            True if verified and enabled
            
        Raises:
            HTTPException: If verification fails
        """
        if not user.totp_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA not initialized. Call enable_2fa first."
            )
        
        # Verify code
        if not totp_manager.verify_totp(user.totp_secret, totp_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid TOTP code"
            )
        
        # Enable 2FA
        user.is_2fa_enabled = True
        db.commit()
        
        logger.info(f"2FA enabled for user: {user.username}")
        return True
    
    def disable_2fa(self, db: Session, user: User) -> bool:
        """
        Disable 2FA for user.
        
        Args:
            db: Database session
            user: User object
            
        Returns:
            True if disabled
        """
        user.is_2fa_enabled = False
        user.totp_secret = None
        db.commit()
        
        logger.info(f"2FA disabled for user: {user.username}")
        return True
