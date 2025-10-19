"""
Role and permission management service.

This service handles role CRUD operations and Casbin policy management.
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import Role, UserRole
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse, PermissionCreate
from app.core.casbin_enforcer import casbin_enforcer
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RoleService:
    """
    Role and permission management service.
    
    Handles role CRUD operations and Casbin policy/permission management.
    """
    
    def create_role(
        self,
        db: Session,
        role_data: RoleCreate
    ) -> Role:
        """
        Create a new role.
        
        Args:
            db: Database session
            role_data: Role creation data
            
        Returns:
            Created role object
            
        Raises:
            HTTPException: If role name already exists
        """
        # Check if role exists
        existing = db.query(Role).filter(Role.name == role_data.name.lower()).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{role_data.name}' already exists"
            )
        
        # Create role
        new_role = Role(
            name=role_data.name.lower(),
            display_name=role_data.display_name,
            description=role_data.description,
            is_system_role=role_data.is_system_role
        )
        
        db.add(new_role)
        db.commit()
        db.refresh(new_role)
        
        logger.info(f"Role created: {new_role.name} (ID: {new_role.id})")
        return new_role
    
    def get_role_by_id(self, db: Session, role_id: int) -> Optional[Role]:
        """
        Get role by ID.
        
        Args:
            db: Database session
            role_id: Role ID
            
        Returns:
            Role object or None
        """
        return db.query(Role).filter(Role.id == role_id).first()
    
    def get_role_by_name(self, db: Session, role_name: str) -> Optional[Role]:
        """
        Get role by name.
        
        Args:
            db: Database session
            role_name: Role name
            
        Returns:
            Role object or None
        """
        return db.query(Role).filter(Role.name == role_name.lower()).first()
    
    def list_roles(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Role], int]:
        """
        List all roles with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (roles list, total count)
        """
        total = db.query(Role).count()
        roles = db.query(Role).offset(skip).limit(limit).all()
        
        return roles, total
    
    def update_role(
        self,
        db: Session,
        role_id: int,
        role_data: RoleUpdate
    ) -> Role:
        """
        Update role information.
        
        Args:
            db: Database session
            role_id: Role ID
            role_data: Update data
            
        Returns:
            Updated role object
            
        Raises:
            HTTPException: If role not found or is system role
        """
        role = self.get_role_by_id(db, role_id)
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        if role.is_system_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify system role"
            )
        
        # Update fields if provided
        if role_data.display_name is not None:
            role.display_name = role_data.display_name
        
        if role_data.description is not None:
            role.description = role_data.description
        
        db.commit()
        db.refresh(role)
        
        logger.info(f"Role updated: {role.name} (ID: {role.id})")
        return role
    
    def delete_role(self, db: Session, role_id: int) -> bool:
        """
        Delete a role.
        
        Args:
            db: Database session
            role_id: Role ID
            
        Returns:
            True if deleted
            
        Raises:
            HTTPException: If role not found or is system role
        """
        role = self.get_role_by_id(db, role_id)
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        if role.is_system_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete system role"
            )
        
        # Check if role is assigned to users
        user_count = db.query(UserRole).filter(UserRole.role_id == role_id).count()
        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete role assigned to {user_count} user(s)"
            )
        
        db.delete(role)
        db.commit()
        
        logger.info(f"Role deleted: {role.name} (ID: {role.id})")
        return True
    
    def get_role_users_count(self, db: Session, role_id: int) -> int:
        """
        Get number of users with this role.
        
        Args:
            db: Database session
            role_id: Role ID
            
        Returns:
            Number of users
        """
        return db.query(UserRole).filter(UserRole.role_id == role_id).count()
    
    def add_permission(
        self,
        permission: PermissionCreate
    ) -> bool:
        """
        Add a permission/policy to Casbin.
        
        Args:
            permission: Permission data
            
        Returns:
            True if added
        """
        success = casbin_enforcer.add_policy(
            subject=permission.subject,
            object=permission.object,
            action=permission.action,
            effect=permission.effect
        )
        
        if success:
            logger.info(f"Permission added: {permission.subject} -> {permission.object} [{permission.action}]")
        else:
            logger.warning(f"Permission already exists or failed to add")
        
        return success
    
    def remove_permission(
        self,
        permission: PermissionCreate
    ) -> bool:
        """
        Remove a permission/policy from Casbin.
        
        Args:
            permission: Permission data
            
        Returns:
            True if removed
        """
        success = casbin_enforcer.remove_policy(
            subject=permission.subject,
            object=permission.object,
            action=permission.action,
            effect=permission.effect
        )
        
        if success:
            logger.info(f"Permission removed: {permission.subject} -> {permission.object} [{permission.action}]")
        else:
            logger.warning(f"Permission not found or failed to remove")
        
        return success
    
    def get_all_permissions(self) -> List[List[str]]:
        """
        Get all permissions from Casbin.
        
        Returns:
            List of policies [subject, object, action, effect]
        """
        return casbin_enforcer.get_all_policies()
    
    def get_role_permissions(self, role_name: str) -> List[List[str]]:
        """
        Get all permissions for a specific role.
        
        Args:
            role_name: Role name
            
        Returns:
            List of policies for this role
        """
        all_policies = casbin_enforcer.get_all_policies()
        return [p for p in all_policies if p[0] == role_name]
    
    def check_permission(
        self,
        user_id: int,
        roles: List[str],
        resource: str,
        action: str
    ) -> bool:
        """
        Check if user has permission based on roles.
        
        Args:
            user_id: User ID
            roles: List of role names
            resource: Resource path
            action: HTTP method
            
        Returns:
            True if permitted, False otherwise
        """
        return casbin_enforcer.check_permission(
            user_id=user_id,
            roles=roles,
            resource=resource,
            action=action
        )
    
    def reload_policies(self) -> bool:
        """
        Reload policies from storage.
        
        Returns:
            True if reloaded successfully
        """
        success = casbin_enforcer.reload_policy()
        
        if success:
            logger.info("Casbin policies reloaded successfully")
        else:
            logger.error("Failed to reload Casbin policies")
        
        return success
    
    def get_users_for_role(self, role_name: str) -> List[str]:
        """
        Get all users assigned to a role in Casbin.
        
        Args:
            role_name: Role name
            
        Returns:
            List of user identifiers
        """
        return casbin_enforcer.get_users_for_role(role_name)
    
    def get_roles_for_user(self, user_id: int) -> List[str]:
        """
        Get all Casbin roles for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of role names
        """
        user_subject = f"user:{user_id}"
        return casbin_enforcer.get_roles_for_user(user_subject)
