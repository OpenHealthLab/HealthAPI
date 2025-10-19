"""
Comprehensive test cases for AuthService.

Tests cover user registration, authentication, token management,
2FA operations, and edge cases.
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.auth_service import AuthService
from app.models.user import User, Role, UserRole, Session as SessionModel
from app.schemas.auth import UserRegister, UserLogin, UserLogin2FA, TokenResponse
from app.core.security import password_hasher, token_manager, totp_manager


class TestAuthService:
    """Test suite for AuthService."""
    
    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance."""
        return AuthService()
    
    @pytest.fixture
    def test_role(self, db: Session):
        """Get the test role (api_user is already seeded by conftest)."""
        role = db.query(Role).filter(Role.name == "api_user").first()
        return role
    
    @pytest.fixture
    def test_user(self, db: Session, test_role):
        """Create a test user."""
        hashed_password = password_hasher.hash_password("TestPassword123!")
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hashed_password,
            full_name="Test User",
            is_active=True,
            oauth_provider="local"
        )
        db.add(user)
        db.flush()
        
        user_role = UserRole(
            user_id=user.id,
            role_id=test_role.id
        )
        db.add(user_role)
        db.commit()
        db.refresh(user)
        return user


class TestRegisterUser(TestAuthService):
    """Tests for register_user method."""
    
    def test_register_user_success(self, db: Session, auth_service: AuthService, test_role):
        """Test successful user registration."""
        user_data = UserRegister(
            username="newuser",
            email="newuser@example.com",
            password="SecurePass123!",
            full_name="New User"
        )
        
        user = auth_service.register_user(db, user_data)
        
        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.is_active is True
        assert user.hashed_password is not None
        assert password_hasher.verify_password("SecurePass123!", user.hashed_password)
    
    def test_register_user_lowercase_username(self, db: Session, auth_service: AuthService, test_role):
        """Test that username is converted to lowercase."""
        user_data = UserRegister(
            username="NewUser",
            email="newuser@example.com",
            password="SecurePass123!",
            full_name="New User"
        )
        
        user = auth_service.register_user(db, user_data)
        assert user.username == "newuser"
    
    def test_register_user_duplicate_username(self, db: Session, auth_service: AuthService, test_user):
        """Test registration with duplicate username fails."""
        user_data = UserRegister(
            username="testuser",
            email="different@example.com",
            password="SecurePass123!",
            full_name="Another User"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.register_user(db, user_data)
        
        assert exc_info.value.status_code == 400
        assert "Username already registered" in str(exc_info.value.detail)
    
    def test_register_user_duplicate_email(self, db: Session, auth_service: AuthService, test_user):
        """Test registration with duplicate email fails."""
        user_data = UserRegister(
            username="differentuser",
            email="test@example.com",
            password="SecurePass123!",
            full_name="Another User"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.register_user(db, user_data)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)
    
    def test_register_user_weak_password(self, db: Session, auth_service: AuthService, test_role):
        """Test registration with weak password fails."""
        from pydantic import ValidationError
        
        # Test password that's too short (< 8 characters) - caught by Pydantic
        with pytest.raises(ValidationError) as exc_info:
            user_data = UserRegister(
                username="newuser",
                email="newuser@example.com",
                password="weak",
                full_name="New User"
            )
        assert "at least 8 characters" in str(exc_info.value)
        
        # Test password that meets length but fails strength requirements - caught by validator
        with pytest.raises(ValidationError) as exc_info:
            user_data = UserRegister(
                username="newuser",
                email="newuser@example.com",
                password="weakpass",  # 8 chars but no uppercase, digit, or special char
                full_name="New User"
            )
        assert "uppercase" in str(exc_info.value).lower() or "digit" in str(exc_info.value).lower()
    
    def test_register_user_with_custom_role(self, db: Session, auth_service: AuthService):
        """Test registration with custom role."""
        custom_role = Role(
            name="custom_role",
            display_name="Custom Role",
            description="Custom role",
            is_system_role=False
        )
        db.add(custom_role)
        db.commit()
        
        user_data = UserRegister(
            username="newuser",
            email="newuser@example.com",
            password="SecurePass123!",
            full_name="New User"
        )
        
        user = auth_service.register_user(db, user_data, default_role="custom_role")
        assert "custom_role" in user.roles


class TestAuthenticateUser(TestAuthService):
    """Tests for authenticate_user method."""
    
    def test_authenticate_user_success(self, db: Session, auth_service: AuthService, test_user):
        """Test successful authentication."""
        user = auth_service.authenticate_user(db, "testuser", "TestPassword123!")
        
        assert user is not None
        assert user.id == test_user.id
        assert user.username == "testuser"
    
    def test_authenticate_user_by_email(self, db: Session, auth_service: AuthService, test_user):
        """Test authentication using email."""
        user = auth_service.authenticate_user(db, "test@example.com", "TestPassword123!")
        
        assert user is not None
        assert user.id == test_user.id
    
    def test_authenticate_user_wrong_password(self, db: Session, auth_service: AuthService, test_user):
        """Test authentication with wrong password."""
        user = auth_service.authenticate_user(db, "testuser", "WrongPassword123!")
        
        assert user is None
    
    def test_authenticate_user_not_found(self, db: Session, auth_service: AuthService):
        """Test authentication with non-existent user."""
        user = auth_service.authenticate_user(db, "nonexistent", "Password123!")
        
        assert user is None
    
    def test_authenticate_inactive_user(self, db: Session, auth_service: AuthService, test_user):
        """Test authentication with inactive user."""
        test_user.is_active = False
        db.commit()
        
        user = auth_service.authenticate_user(db, "testuser", "TestPassword123!")
        
        assert user is None
    
    def test_authenticate_oauth_user_no_password(self, db: Session, auth_service: AuthService, test_role):
        """Test authentication fails for OAuth users without password."""
        oauth_user = User(
            username="oauthuser",
            email="oauth@example.com",
            hashed_password=None,
            full_name="OAuth User",
            is_active=True,
            oauth_provider="google"
        )
        db.add(oauth_user)
        db.commit()
        
        user = auth_service.authenticate_user(db, "oauthuser", "AnyPassword123!")
        
        assert user is None


class TestCreateUserTokens(TestAuthService):
    """Tests for create_user_tokens method."""
    
    def test_create_user_tokens_success(self, db: Session, auth_service: AuthService, test_user):
        """Test successful token creation."""
        tokens = auth_service.create_user_tokens(
            db, test_user,
            ip_address="127.0.0.1",
            user_agent="TestAgent"
        )
        
        assert isinstance(tokens, TokenResponse)
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"
        assert tokens.expires_in == 15 * 60
        
        # Verify session created
        session = db.query(SessionModel).filter(
            SessionModel.user_id == test_user.id
        ).first()
        assert session is not None
        assert session.ip_address == "127.0.0.1"
        assert session.user_agent == "TestAgent"
        assert session.is_valid is True
    
    def test_create_user_tokens_updates_last_login(self, db: Session, auth_service: AuthService, test_user):
        """Test that token creation updates last login time."""
        old_login = test_user.last_login
        
        auth_service.create_user_tokens(db, test_user)
        
        db.refresh(test_user)
        assert test_user.last_login is not None
        assert test_user.last_login != old_login
    
    def test_create_user_tokens_with_roles(self, db: Session, auth_service: AuthService, test_user):
        """Test that tokens contain user roles."""
        tokens = auth_service.create_user_tokens(db, test_user)
        
        payload = token_manager.decode_token(tokens.access_token)
        assert "roles" in payload
        assert "api_user" in payload["roles"]


class TestLogin(TestAuthService):
    """Tests for login method."""
    
    def test_login_success(self, db: Session, auth_service: AuthService, test_user):
        """Test successful login."""
        credentials = UserLogin(
            username="testuser",
            password="TestPassword123!"
        )
        
        tokens, requires_2fa = auth_service.login(db, credentials)
        
        assert requires_2fa is False
        assert tokens is not None
        assert isinstance(tokens, TokenResponse)
    
    def test_login_wrong_credentials(self, db: Session, auth_service: AuthService, test_user):
        """Test login with wrong credentials."""
        credentials = UserLogin(
            username="testuser",
            password="WrongPassword123!"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login(db, credentials)
        
        assert exc_info.value.status_code == 401
        assert "Incorrect username or password" in str(exc_info.value.detail)
    
    def test_login_requires_2fa(self, db: Session, auth_service: AuthService, test_user):
        """Test login returns 2FA requirement."""
        test_user.is_2fa_enabled = True
        test_user.totp_secret = "test_secret"
        db.commit()
        
        credentials = UserLogin(
            username="testuser",
            password="TestPassword123!"
        )
        
        tokens, requires_2fa = auth_service.login(db, credentials)
        
        assert requires_2fa is True
        assert tokens is None


class TestLoginWith2FA(TestAuthService):
    """Tests for login_with_2fa method."""
    
    def test_login_with_2fa_success(self, db: Session, auth_service: AuthService, test_user, mocker):
        """Test successful 2FA login."""
        test_user.is_2fa_enabled = True
        test_user.totp_secret = totp_manager.generate_secret()
        db.commit()
        
        # Mock TOTP verification
        mocker.patch.object(totp_manager, 'verify_totp', return_value=True)
        
        credentials = UserLogin2FA(
            username="testuser",
            password="TestPassword123!",
            totp_code="123456"
        )
        
        tokens = auth_service.login_with_2fa(db, credentials)
        
        assert isinstance(tokens, TokenResponse)
        assert tokens.access_token is not None
    
    def test_login_with_2fa_invalid_code(self, db: Session, auth_service: AuthService, test_user, mocker):
        """Test 2FA login with invalid code."""
        test_user.is_2fa_enabled = True
        test_user.totp_secret = totp_manager.generate_secret()
        db.commit()
        
        # Mock TOTP verification to fail
        mocker.patch.object(totp_manager, 'verify_totp', return_value=False)
        
        credentials = UserLogin2FA(
            username="testuser",
            password="TestPassword123!",
            totp_code="000000"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login_with_2fa(db, credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid 2FA code" in str(exc_info.value.detail)
    
    def test_login_with_2fa_not_enabled(self, db: Session, auth_service: AuthService, test_user):
        """Test 2FA login when 2FA not enabled."""
        credentials = UserLogin2FA(
            username="testuser",
            password="TestPassword123!",
            totp_code="123456"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login_with_2fa(db, credentials)
        
        assert exc_info.value.status_code == 400
        assert "2FA not enabled" in str(exc_info.value.detail)


class TestLogout(TestAuthService):
    """Tests for logout method."""
    
    def test_logout_success(self, db: Session, auth_service: AuthService, test_user):
        """Test successful logout."""
        # Create session
        tokens = auth_service.create_user_tokens(db, test_user)
        payload = token_manager.decode_token(tokens.access_token)
        jti = payload["jti"]
        
        # Logout
        result = auth_service.logout(db, jti)
        
        assert result is True
        
        # Verify session invalidated
        session = db.query(SessionModel).filter(
            SessionModel.jti == jti
        ).first()
        assert session.is_valid is False
    
    def test_logout_invalid_jti(self, db: Session, auth_service: AuthService):
        """Test logout with invalid JTI."""
        result = auth_service.logout(db, "invalid_jti")
        
        assert result is False


class TestRefreshAccessToken(TestAuthService):
    """Tests for refresh_access_token method."""
    
    def test_refresh_token_success(self, db: Session, auth_service: AuthService, test_user):
        """Test successful token refresh."""
        # Create initial tokens
        initial_tokens = auth_service.create_user_tokens(db, test_user)
        
        # Refresh tokens
        new_tokens = auth_service.refresh_access_token(db, initial_tokens.refresh_token)
        
        assert isinstance(new_tokens, TokenResponse)
        assert new_tokens.access_token != initial_tokens.access_token
        assert new_tokens.refresh_token != initial_tokens.refresh_token
    
    def test_refresh_token_invalid(self, db: Session, auth_service: AuthService):
        """Test refresh with invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_access_token(db, "invalid_token")
        
        assert exc_info.value.status_code == 401
    
    def test_refresh_token_inactive_user(self, db: Session, auth_service: AuthService, test_user):
        """Test refresh token with inactive user."""
        tokens = auth_service.create_user_tokens(db, test_user)
        
        # Deactivate user
        test_user.is_active = False
        db.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_access_token(db, tokens.refresh_token)
        
        assert exc_info.value.status_code == 401
        assert "inactive" in str(exc_info.value.detail).lower()


class TestEnable2FA(TestAuthService):
    """Tests for 2FA methods."""
    
    def test_enable_2fa_generates_secret(self, db: Session, auth_service: AuthService, test_user):
        """Test enabling 2FA generates secret and QR code."""
        result = auth_service.enable_2fa(db, test_user)
        
        assert "secret" in result
        assert "qr_code" in result
        assert result["secret"] is not None
        assert result["qr_code"] is not None
        
        db.refresh(test_user)
        assert test_user.totp_secret is not None
        assert test_user.is_2fa_enabled is False  # Not enabled until verified
    
    def test_verify_and_enable_2fa_success(self, db: Session, auth_service: AuthService, test_user, mocker):
        """Test verifying and enabling 2FA."""
        # Generate secret
        auth_service.enable_2fa(db, test_user)
        
        # Mock TOTP verification
        mocker.patch.object(totp_manager, 'verify_totp', return_value=True)
        
        result = auth_service.verify_and_enable_2fa(db, test_user, "123456")
        
        assert result is True
        db.refresh(test_user)
        assert test_user.is_2fa_enabled is True
    
    def test_verify_and_enable_2fa_invalid_code(self, db: Session, auth_service: AuthService, test_user, mocker):
        """Test verifying 2FA with invalid code."""
        # Generate secret
        auth_service.enable_2fa(db, test_user)
        
        # Mock TOTP verification to fail
        mocker.patch.object(totp_manager, 'verify_totp', return_value=False)
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_and_enable_2fa(db, test_user, "000000")
        
        assert exc_info.value.status_code == 400
        assert "Invalid TOTP code" in str(exc_info.value.detail)
    
    def test_verify_and_enable_2fa_not_initialized(self, db: Session, auth_service: AuthService, test_user):
        """Test verifying 2FA before initialization."""
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_and_enable_2fa(db, test_user, "123456")
        
        assert exc_info.value.status_code == 400
        assert "not initialized" in str(exc_info.value.detail)
    
    def test_disable_2fa(self, db: Session, auth_service: AuthService, test_user):
        """Test disabling 2FA."""
        # Enable 2FA first
        test_user.is_2fa_enabled = True
        test_user.totp_secret = "test_secret"
        db.commit()
        
        result = auth_service.disable_2fa(db, test_user)
        
        assert result is True
        db.refresh(test_user)
        assert test_user.is_2fa_enabled is False
        assert test_user.totp_secret is None


class TestEdgeCases(TestAuthService):
    """Tests for edge cases and error handling."""
    
    def test_multiple_sessions_same_user(self, db: Session, auth_service: AuthService, test_user):
        """Test creating multiple sessions for same user."""
        tokens1 = auth_service.create_user_tokens(db, test_user, ip_address="192.168.1.1")
        tokens2 = auth_service.create_user_tokens(db, test_user, ip_address="192.168.1.2")
        
        sessions = db.query(SessionModel).filter(
            SessionModel.user_id == test_user.id,
            SessionModel.is_valid == True
        ).all()
        
        assert len(sessions) == 2
    
    def test_token_expiration_stored_correctly(self, db: Session, auth_service: AuthService, test_user):
        """Test that token expiration is stored correctly in session."""
        tokens = auth_service.create_user_tokens(db, test_user)
        
        session = db.query(SessionModel).filter(
            SessionModel.user_id == test_user.id
        ).first()
        
        assert session.expires_at is not None
        # Handle both timezone-aware and timezone-naive datetimes
        current_time = datetime.now(timezone.utc)
        if session.expires_at.tzinfo is None:
            # If session.expires_at is naive, compare with naive datetime
            current_time = datetime.utcnow()
        assert session.expires_at > current_time
    
    def test_case_insensitive_username_authentication(self, db: Session, auth_service: AuthService, test_user):
        """Test authentication works with different case usernames."""
        user = auth_service.authenticate_user(db, "TESTUSER", "TestPassword123!")
        
        assert user is not None
        assert user.id == test_user.id
