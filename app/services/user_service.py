"""
User management service.

This service handles user CRUD operations, role assignments,
and user profile management.
"""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.user import User, Role, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserStats
from app.core.security import password_hasher
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class UserService:
    """
    User management service.
    
    Handles user CRUD operations, profile management,
    and role assignments.
    """
    
    def create_user(
        self,
        db: Session,
        user_data: UserCreate,
        created_by: Optional[int] = None
    ) -> User:
        """
        Create a new user (admin operation).
        
        Args:
            db: Database session
            user_data: User creation data
            created_by: User ID of admin creating the user
            
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Check if email exists
        existing_email = db.query(User).filter(
            User.email == user_data.email
        ).first()
        
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
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
            is_active=user_data.is_active,
            is_superuser=user_data.is_superuser,
            oauth_provider="local"
        )
        
        db.add(new_user)
        db.flush()  # Get user ID
        
        # Assign roles
        if user_data.roles:
            for role_name in user_data.roles:
                role = db.query(Role).filter(Role.name == role_name).first()
                if role:
                    user_role = UserRole(
                        user_id=new_user.id,
                        role_id=role.id,
                        assigned_by=created_by
                    )
                    db.add(user_role)
                else:
                    logger.warning(f"Role '{role_name}' not found")
        
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"User created: {new_user.username} (ID: {new_user.id})")
        return new_user
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User object or None
        """
        return db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            db: Database session
            username: Username
            
        Returns:
            User object or None
        """
        return db.query(User).filter(User.username == username.lower()).first()
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            db: Database session
            email: Email address
            
        Returns:
            User object or None
        """
        return db.query(User).filter(User.email == email).first()
    
    def list_users(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> Tuple[List[User], int]:
        """
        List users with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            is_active: Filter by active status
            
        Returns:
            Tuple of (users list, total count)
        """
        query = db.query(User)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        total = query.count()
        users = query.offset(skip).limit(limit).all()
        
        return users, total
    
    def update_user(
        self,
        db: Session,
        user_id: int,
        user_data: UserUpdate
    ) -> User:
        """
        Update user information.
        
        Args:
            db: Database session
            user_id: User ID
            user_data: Update data
            
        Returns:
            Updated user object
            
        Raises:
            HTTPException: If user not found or email already exists
        """
        user = self.get_user_by_id(db, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields if provided
        if user_data.email is not None:
            # Check if email already exists for another user
            existing = db.query(User).filter(
                User.email == user_data.email,
                User.id != user_id
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            
            user.email = user_data.email
        
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        if user_data.is_superuser is not None:
            user.is_superuser = user_data.is_superuser
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User updated: {user.username} (ID: {user.id})")
        return user
    
    def delete_user(self, db: Session, user_id: int) -> bool:
        """
        Delete user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            True if deleted
            
        Raises:
            HTTPException: If user not found
        """
        user = self.get_user_by_id(db, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        db.delete(user)
        db.commit()
        
        logger.info(f"User deleted: {user.username} (ID: {user.id})")
        return True
    
    def assign_role(
        self,
        db: Session,
        user_id: int,
        role_name: str,
        assigned_by: Optional[int] = None
    ) -> bool:
        """
        Assign role to user.
        
        Args:
            db: Database session
            user_id: User ID
            role_name: Role name to assign
            assigned_by: User ID of admin assigning the role
            
        Returns:
            True if assigned
            
        Raises:
            HTTPException: If user or role not found, or already assigned
        """
        user = self.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_name}' not found"
            )
        
        # Check if already assigned
        existing = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role.id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User already has role '{role_name}'"
            )
        
        # Assign role
        user_role = UserRole(
            user_id=user_id,
            role_id=role.id,
            assigned_by=assigned_by
        )
        
        db.add(user_role)
        db.commit()
        
        logger.info(f"Role '{role_name}' assigned to user {user.username}")
        return True
    
    def remove_role(
        self,
        db: Session,
        user_id: int,
        role_name: str
    ) -> bool:
        """
        Remove role from user.
        
        Args:
            db: Database session
            user_id: User ID
            role_name: Role name to remove
            
        Returns:
            True if removed
            
        Raises:
            HTTPException: If user or role not found, or not assigned
        """
        user = self.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_name}' not found"
            )
        
        # Find assignment
        user_role = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role.id
        ).first()
        
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User does not have role '{role_name}'"
            )
        
        # Remove role
        db.delete(user_role)
        db.commit()
        
        logger.info(f"Role '{role_name}' removed from user {user.username}")
        return True
    
    def get_user_roles(self, db: Session, user_id: int) -> List[str]:
        """
        Get all roles for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of role names
        """
        user = self.get_user_by_id(db, user_id)
        if not user:
            return []
        
        return [ur.role.name for ur in user.user_roles]
    
    def change_password(
        self,
        db: Session,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password.
        
        Args:
            db: Database session
            user_id: User ID
            current_password: Current password
            new_password: New password
            
        Returns:
            True if changed
            
        Raises:
            HTTPException: If user not found or password invalid
        """
        user = self.get_user_by_id(db, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not user.hashed_password or not password_hasher.verify_password(
            current_password, user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid current password"
            )
        
        # Validate new password
        is_valid, error_msg = password_hasher.validate_password_strength(new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Update password
        user.hashed_password = password_hasher.hash_password(new_password)
        db.commit()
        
        logger.info(f"Password changed for user: {user.username}")
        return True
    
    def get_user_stats(self, db: Session) -> UserStats:
        """
        Get user statistics.
        
        Args:
            db: Database session
            
        Returns:
            UserStats object
        """
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        inactive_users = total_users - active_users
        users_with_2fa = db.query(User).filter(User.is_2fa_enabled == True).count()
        oauth_users = db.query(User).filter(User.oauth_provider != "local").count()
        
        return UserStats(
            total_users=total_users,
            active_users=active_users,
            inactive_users=inactive_users,
            users_with_2fa=users_with_2fa,
            oauth_users=oauth_users
        )
