"""
User authentication and authorization models.

This module defines SQLAlchemy ORM models for user management,
roles, and RBAC (Role-Based Access Control).
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from typing import List as ListType


class User(Base):
    """
    User model for authentication and authorization.
    
    Supports both local authentication (username/password) and
    OAuth2 providers (Google). Includes 2FA support with TOTP.
    
    Attributes:
        id: Primary key
        username: Unique username
        email: Unique email address
        hashed_password: Bcrypt hashed password (nullable for OAuth users)
        full_name: User's full name
        is_active: Whether user account is active
        is_superuser: Whether user has superuser privileges
        oauth_provider: OAuth provider name ('google', 'local', None)
        oauth_id: OAuth provider user ID
        totp_secret: Secret key for TOTP 2FA
        is_2fa_enabled: Whether 2FA is enabled for user
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        last_login: Last successful login timestamp
    """
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # OAuth fields
    oauth_provider = Column(String, nullable=True)  # 'google', 'local', None
    oauth_id = Column(String, nullable=True)
    
    # 2FA fields
    totp_secret = Column(String, nullable=True)
    is_2fa_enabled = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user_roles = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="UserRole.user_id",
        primaryjoin="User.id == UserRole.user_id"
    )
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def roles(self) -> ListType[str]:
        """Get list of role names for this user."""
        return [ur.role.name for ur in self.user_roles]
    
    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Role(Base):
    """
    Role model for RBAC.
    
    Defines roles that can be assigned to users for access control.
    System roles (like 'superadmin', 'admin') cannot be deleted.
    
    Attributes:
        id: Primary key
        name: Unique role name (lowercase, e.g., 'doctor', 'admin')
        display_name: Human-readable role name (e.g., 'Doctor', 'Administrator')
        description: Role description
        is_system_role: Whether this is a protected system role
        created_at: Creation timestamp
    """
    
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_system_role = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    users = relationship("UserRole", back_populates="role", cascade="all, delete-orphan", foreign_keys="[UserRole.role_id]")
    
    def __repr__(self) -> str:
        """String representation of Role."""
        return f"<Role(id={self.id}, name='{self.name}')>"


class UserRole(Base):
    """
    Junction table for User-Role many-to-many relationship.
    
    Tracks role assignments to users, including when and by whom
    the role was assigned.
    
    Attributes:
        user_id: Foreign key to User
        role_id: Foreign key to Role
        assigned_at: When role was assigned
        assigned_by: User ID who assigned this role
    """
    
    __tablename__ = "user_roles"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role = relationship("Role", back_populates="users")
    assigner = relationship("User", foreign_keys=[assigned_by])
    
    def __repr__(self) -> str:
        """String representation of UserRole."""
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


class Session(Base):
    """
    Session model for tracking JWT tokens.
    
    Stores active sessions and allows for token invalidation/blacklisting.
    Used for logout functionality and session management.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User
        jti: JWT ID (unique token identifier)
        refresh_token: Refresh token hash
        is_valid: Whether session is still valid
        ip_address: IP address of client
        user_agent: User agent string
        expires_at: When session expires
        created_at: Session creation timestamp
    """
    
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    jti = Column(String, unique=True, nullable=False, index=True)
    refresh_token = Column(String, unique=True, nullable=False)
    is_valid = Column(Boolean, default=True, nullable=False, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self) -> str:
        """String representation of Session."""
        return f"<Session(id={self.id}, user_id={self.user_id}, is_valid={self.is_valid})>"


class AuditLog(Base):
    """
    Audit log model for compliance and security tracking.
    
    Records all significant actions performed by users for
    security auditing and compliance (e.g., HIPAA).
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User (nullable for anonymous actions)
        action: Action performed (e.g., 'login', 'create_prediction')
        resource: Resource type (e.g., 'auth', 'prediction')
        resource_id: Specific resource ID (optional)
        details: Additional JSON details
        ip_address: IP address of client
        user_agent: User agent string
        status: Action status ('success', 'failure')
        timestamp: When action occurred
    """
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String, nullable=False, index=True)
    resource = Column(String, nullable=False, index=True)
    resource_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)  # JSON string with additional context
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    status = Column(String, nullable=False, index=True)  # 'success', 'failure'
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self) -> str:
        """String representation of AuditLog."""
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action='{self.action}')>"
