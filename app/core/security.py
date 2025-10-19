"""
Security utilities for authentication and authorization.


This module provides utilities for:
- Password hashing and verification
- JWT token creation and validation
- 2FA TOTP generation and verification
"""


from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import secrets
import hashlib


from jose import JWTError, jwt
from pwdlib import PasswordHash
import pyotp
import qrcode
from io import BytesIO
import base64


from app.core.config import get_settings


settings = get_settings()


# Password hashing context
# Use Argon2 for password hashing (secure and modern algorithm)
pwd_hash = PasswordHash.recommended()


# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7



class PasswordHasher:
    """
    Password hashing and verification utility.
    
    Uses Argon2 for secure password hashing.
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plaintext password.
        
        Args:
            password: Plaintext password
            
        Returns:
            Hashed password string
        """
        return pwd_hash.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plaintext password to verify
            hashed_password: Hashed password to check against
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_hash.verify(plain_password, hashed_password)
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
        """
        Validate password meets security requirements.
        
        Requirements:
        - At least 8 characters
        - Contains uppercase letter
        - Contains lowercase letter
        - Contains digit
        - Contains special character
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return False, "Password must contain at least one special character"
        
        return True, None



class TokenManager:
    """
    JWT token creation and validation manager.
    
    Handles both access tokens (short-lived) and refresh tokens (long-lived).
    """
    
    def __init__(self, secret_key: str = None):
        """
        Initialize token manager.
        
        Args:
            secret_key: Secret key for JWT signing (defaults to settings)
        """
        self.secret_key = secret_key or settings.secret_key
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Data to encode in token (should include 'sub' for user_id)
            expires_delta: Custom expiration time (default: 15 minutes)
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
            "jti": self._generate_jti()
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT refresh token.
        
        Args:
            data: Data to encode in token (should include 'sub' for user_id)
            expires_delta: Custom expiration time (default: 7 days)
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
            "jti": self._generate_jti()
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=ALGORITHM)
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Verify token is valid and of correct type.
        
        Args:
            token: JWT token string
            token_type: Expected token type ('access' or 'refresh')
            
        Returns:
            Decoded payload if valid, None otherwise
        """
        payload = self.decode_token(token)
        
        if not payload:
            return None
        
        if payload.get("type") != token_type:
            return None
        
        return payload
    
    @staticmethod
    def _generate_jti() -> str:
        """Generate a unique JWT ID."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash a token for secure storage.
        
        Args:
            token: Token to hash
            
        Returns:
            SHA256 hash of token
        """
        return hashlib.sha256(token.encode()).hexdigest()



class TOTPManager:
    """
    Time-based One-Time Password (TOTP) manager for 2FA.
    
    Handles generation and verification of TOTP codes.
    """
    
    @staticmethod
    def generate_secret() -> str:
        """
        Generate a new TOTP secret key.
        
        Returns:
            Base32-encoded secret key
        """
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(
        secret: str,
        username: str,
        issuer: str = "HealthAPI"
    ) -> str:
        """
        Generate QR code for TOTP setup.
        
        Args:
            secret: TOTP secret key
            username: Username or email
            issuer: Application name
            
        Returns:
            Base64-encoded QR code image
        """
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=username, issuer_name=issuer)
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def verify_totp(secret: str, token: str, window: int = 1) -> bool:
        """
        Verify a TOTP token.
        
        Args:
            secret: TOTP secret key
            token: 6-digit TOTP code
            window: Number of time windows to check (default: 1)
            
        Returns:
            True if token is valid, False otherwise
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=window)
    
    @staticmethod
    def get_current_totp(secret: str) -> str:
        """
        Get current TOTP code (for testing/debugging).
        
        Args:
            secret: TOTP secret key
            
        Returns:
            Current 6-digit TOTP code
        """
        totp = pyotp.TOTP(secret)
        return totp.now()



# Singleton instances
password_hasher = PasswordHasher()
token_manager = TokenManager()
totp_manager = TOTPManager()
