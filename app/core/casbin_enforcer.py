"""
Casbin enforcer wrapper for RBAC.

This module provides the Casbin enforcer for role-based access control,
including methods to check permissions and manage policies.
"""

import os
from typing import List, Optional
import casbin
from casbin_sqlalchemy_adapter import Adapter
from sqlalchemy import create_engine

from app.core.config import get_settings
from app.core.logging_config import get_logger

settings = get_settings()
logger = get_logger(__name__)


class CasbinEnforcer:
    """
    Casbin enforcer wrapper for RBAC.
    
    Manages policy enforcement and provides methods for
    checking permissions and managing policies.
    """
    
    def __init__(self, model_path: str = None, policy_path: str = None):
        """
        Initialize Casbin enforcer.
        
        Args:
            model_path: Path to Casbin model file
            policy_path: Path to Casbin policy file
        """
        self.model_path = model_path or "casbin/model.conf"
        self.policy_path = policy_path or "casbin/policy.csv"
        self.enforcer: Optional[casbin.Enforcer] = None
        
    def initialize(self):
        """
        Initialize the Casbin enforcer.
        
        Loads the model and policies from files.
        """
        try:
            # Check if model file exists
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Casbin model file not found: {self.model_path}")
            
            # For development, use file adapter (CSV)
            # For production, consider using database adapter
            if os.path.exists(self.policy_path):
                self.enforcer = casbin.Enforcer(self.model_path, self.policy_path)
                logger.info(f"✓ Casbin enforcer initialized with CSV adapter")
            else:
                # Initialize with empty policy
                self.enforcer = casbin.Enforcer(self.model_path)
                logger.warning(f"Casbin policy file not found: {self.policy_path}")
                logger.info("✓ Casbin enforcer initialized with empty policy")
            
            logger.info(f"Loaded {len(self.enforcer.get_policy())} policies")
            logger.info(f"Loaded {len(self.enforcer.get_grouping_policy())} role assignments")
            
        except Exception as e:
            logger.error(f"Failed to initialize Casbin enforcer: {e}", exc_info=True)
            raise
    
    def enforce(self, subject: str, object: str, action: str) -> bool:
        """
        Check if a subject has permission to perform action on object.
        
        Args:
            subject: User or role identifier
            object: Resource path (e.g., '/api/v1/predict')
            action: HTTP method (e.g., 'GET', 'POST')
            
        Returns:
            True if permitted, False otherwise
        """
        if not self.enforcer:
            logger.error("Casbin enforcer not initialized")
            return False
        
        try:
            result = self.enforcer.enforce(subject, object, action)
            logger.debug(f"Permission check: {subject} -> {object} [{action}] = {result}")
            return result
        except Exception as e:
            logger.error(f"Error checking permission: {e}", exc_info=True)
            return False
    
    def check_permission(
        self,
        user_id: int,
        roles: List[str],
        resource: str,
        action: str
    ) -> bool:
        """
        Check if user has permission based on their roles.
        
        Args:
            user_id: User ID
            roles: List of role names
            resource: Resource path
            action: HTTP method
            
        Returns:
            True if user has permission, False otherwise
        """
        # Check direct user permission
        user_subject = f"user:{user_id}"
        if self.enforce(user_subject, resource, action):
            return True
        
        # Check role permissions
        for role in roles:
            if self.enforce(role, resource, action):
                return True
        
        return False
    
    def add_policy(self, subject: str, object: str, action: str, effect: str = "allow") -> bool:
        """
        Add a new policy.
        
        Args:
            subject: Role or user
            object: Resource path
            action: HTTP method
            effect: 'allow' or 'deny'
            
        Returns:
            True if added successfully, False otherwise
        """
        if not self.enforcer:
            return False
        
        try:
            result = self.enforcer.add_policy(subject, object, action, effect)
            if result:
                self.save_policy()
                logger.info(f"Added policy: {subject} -> {object} [{action}] = {effect}")
            return result
        except Exception as e:
            logger.error(f"Error adding policy: {e}", exc_info=True)
            return False
    
    def remove_policy(self, subject: str, object: str, action: str, effect: str = "allow") -> bool:
        """
        Remove a policy.
        
        Args:
            subject: Role or user
            object: Resource path
            action: HTTP method
            effect: 'allow' or 'deny'
            
        Returns:
            True if removed successfully, False otherwise
        """
        if not self.enforcer:
            return False
        
        try:
            result = self.enforcer.remove_policy(subject, object, action, effect)
            if result:
                self.save_policy()
                logger.info(f"Removed policy: {subject} -> {object} [{action}] = {effect}")
            return result
        except Exception as e:
            logger.error(f"Error removing policy: {e}", exc_info=True)
            return False
    
    def add_role_for_user(self, user: str, role: str) -> bool:
        """
        Assign a role to a user.
        
        Args:
            user: User identifier (e.g., 'user:123')
            role: Role name (e.g., 'doctor')
            
        Returns:
            True if added successfully, False otherwise
        """
        if not self.enforcer:
            return False
        
        try:
            result = self.enforcer.add_grouping_policy(user, role)
            if result:
                self.save_policy()
                logger.info(f"Assigned role '{role}' to user '{user}'")
            return result
        except Exception as e:
            logger.error(f"Error assigning role: {e}", exc_info=True)
            return False
    
    def remove_role_for_user(self, user: str, role: str) -> bool:
        """
        Remove a role from a user.
        
        Args:
            user: User identifier
            role: Role name
            
        Returns:
            True if removed successfully, False otherwise
        """
        if not self.enforcer:
            return False
        
        try:
            result = self.enforcer.remove_grouping_policy(user, role)
            if result:
                self.save_policy()
                logger.info(f"Removed role '{role}' from user '{user}'")
            return result
        except Exception as e:
            logger.error(f"Error removing role: {e}", exc_info=True)
            return False
    
    def get_roles_for_user(self, user: str) -> List[str]:
        """
        Get all roles assigned to a user.
        
        Args:
            user: User identifier
            
        Returns:
            List of role names
        """
        if not self.enforcer:
            return []
        
        try:
            return self.enforcer.get_roles_for_user(user)
        except Exception as e:
            logger.error(f"Error getting roles for user: {e}", exc_info=True)
            return []
    
    def get_users_for_role(self, role: str) -> List[str]:
        """
        Get all users with a specific role.
        
        Args:
            role: Role name
            
        Returns:
            List of user identifiers
        """
        if not self.enforcer:
            return []
        
        try:
            return self.enforcer.get_users_for_role(role)
        except Exception as e:
            logger.error(f"Error getting users for role: {e}", exc_info=True)
            return []
    
    def get_all_policies(self) -> List[List[str]]:
        """
        Get all policies.
        
        Returns:
            List of policies [subject, object, action, effect]
        """
        if not self.enforcer:
            return []
        
        return self.enforcer.get_policy()
    
    def get_all_roles(self) -> List[List[str]]:
        """
        Get all role assignments.
        
        Returns:
            List of role assignments [user, role]
        """
        if not self.enforcer:
            return []
        
        return self.enforcer.get_grouping_policy()
    
    def save_policy(self) -> bool:
        """
        Save current policies to file/database.
        
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.enforcer:
            return False
        
        try:
            self.enforcer.save_policy()
            return True
        except Exception as e:
            logger.error(f"Error saving policy: {e}", exc_info=True)
            return False
    
    def reload_policy(self) -> bool:
        """
        Reload policies from file/database.
        
        Returns:
            True if reloaded successfully, False otherwise
        """
        if not self.enforcer:
            return False
        
        try:
            self.enforcer.load_policy()
            logger.info("Policies reloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error reloading policy: {e}", exc_info=True)
            return False


# Singleton instance
casbin_enforcer = CasbinEnforcer()
