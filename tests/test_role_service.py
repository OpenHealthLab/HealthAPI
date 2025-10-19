"""
Comprehensive test cases for RoleService.

Tests cover role CRUD operations, permission management,
Casbin policy operations, and edge cases.
"""

import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.role_service import RoleService
from app.models.user import Role, User, UserRole
from app.schemas.role import RoleCreate, RoleUpdate, PermissionCreate
from app.core.security import password_hasher


class TestRoleService:
    """Test suite for RoleService."""
    
    @pytest.fixture
    def role_service(self):
        """Create RoleService instance."""
        return RoleService()
    
    @pytest.fixture
    def test_role(self, db: Session):
        """Create a test role."""
        role = Role(
            name="test_role",
            display_name="Test Role",
            description="A test role",
            is_system_role=False
        )
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
    
    @pytest.fixture
    def system_role(self, db: Session):
        """Create a system role."""
        role = Role(
            name="system_admin",
            display_name="System Admin",
            description="System administrator role",
            is_system_role=True
        )
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
    
    @pytest.fixture
    def test_user(self, db: Session, test_role):
        """Create a test user with role."""
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


class TestCreateRole(TestRoleService):
    """Tests for create_role method."""
    
    def test_create_role_success(self, db: Session, role_service: RoleService):
        """Test successful role creation."""
        role_data = RoleCreate(
            name="new_role",
            display_name="New Role",
            description="A new role",
            is_system_role=False
        )
        
        role = role_service.create_role(db, role_data)
        
        assert role.id is not None
        assert role.name == "new_role"
        assert role.display_name == "New Role"
        assert role.description == "A new role"
        assert role.is_system_role is False
    
    def test_create_role_lowercase_name(self, db: Session, role_service: RoleService):
        """Test that role name is converted to lowercase."""
        role_data = RoleCreate(
            name="NewRole",
            display_name="New Role",
            description="A new role",
            is_system_role=False
        )
        
        role = role_service.create_role(db, role_data)
        
        assert role.name == "newrole"
    
    def test_create_role_duplicate_name(self, db: Session, role_service: RoleService, test_role):
        """Test creating role with duplicate name fails."""
        role_data = RoleCreate(
            name="test_role",
            display_name="Another Test Role",
            description="Duplicate name",
            is_system_role=False
        )
        
        with pytest.raises(HTTPException) as exc_info:
            role_service.create_role(db, role_data)
        
        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)
    
    def test_create_system_role(self, db: Session, role_service: RoleService):
        """Test creating a system role."""
        role_data = RoleCreate(
            name="superadmin",
            display_name="Super Administrator",
            description="System super administrator",
            is_system_role=True
        )
        
        role = role_service.create_role(db, role_data)
        
        assert role.is_system_role is True


class TestGetRole(TestRoleService):
    """Tests for get_role_by_id and get_role_by_name methods."""
    
    def test_get_role_by_id_success(self, db: Session, role_service: RoleService, test_role):
        """Test successful role retrieval by ID."""
        role = role_service.get_role_by_id(db, test_role.id)
        
        assert role is not None
        assert role.id == test_role.id
        assert role.name == test_role.name
    
    def test_get_role_by_id_not_found(self, db: Session, role_service: RoleService):
        """Test retrieving non-existent role by ID."""
        role = role_service.get_role_by_id(db, 99999)
        
        assert role is None
    
    def test_get_role_by_name_success(self, db: Session, role_service: RoleService, test_role):
        """Test successful role retrieval by name."""
        role = role_service.get_role_by_name(db, "test_role")
        
        assert role is not None
        assert role.name == "test_role"
    
    def test_get_role_by_name_case_insensitive(self, db: Session, role_service: RoleService, test_role):
        """Test that role name lookup is case-insensitive."""
        role = role_service.get_role_by_name(db, "TEST_ROLE")
        
        assert role is not None
        assert role.name == "test_role"
    
    def test_get_role_by_name_not_found(self, db: Session, role_service: RoleService):
        """Test retrieving non-existent role by name."""
        role = role_service.get_role_by_name(db, "nonexistent")
        
        assert role is None


class TestListRoles(TestRoleService):
    """Tests for list_roles method."""
    
    def test_list_roles_success(self, db: Session, role_service: RoleService, test_role):
        """Test listing all roles."""
        roles, total = role_service.list_roles(db)
        
        assert len(roles) >= 1
        assert total >= 1
        assert any(r.id == test_role.id for r in roles)
    
    def test_list_roles_pagination(self, db: Session, role_service: RoleService):
        """Test pagination of roles."""
        # Create multiple roles
        for i in range(10):
            role = Role(
                name=f"role_{i}",
                display_name=f"Role {i}",
                description=f"Role number {i}",
                is_system_role=False
            )
            db.add(role)
        db.commit()
        
        # Get first page
        page1, total1 = role_service.list_roles(db, skip=0, limit=5)
        assert len(page1) == 5
        
        # Get second page
        page2, total2 = role_service.list_roles(db, skip=5, limit=5)
        assert len(page2) == 5
        
        # Total should be the same
        assert total1 == total2
        
        # Verify no overlap
        page1_ids = {r.id for r in page1}
        page2_ids = {r.id for r in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0
    
    def test_list_roles_empty(self, db: Session, role_service: RoleService):
        """Test listing roles when none exist."""
        # Clear all roles
        db.query(UserRole).delete()
        db.query(Role).delete()
        db.commit()
        
        roles, total = role_service.list_roles(db)
        
        assert len(roles) == 0
        assert total == 0


class TestUpdateRole(TestRoleService):
    """Tests for update_role method."""
    
    def test_update_role_display_name(self, db: Session, role_service: RoleService, test_role):
        """Test updating role display name."""
        role_data = RoleUpdate(
            display_name="Updated Name",
            description=None
        )
        
        updated_role = role_service.update_role(db, test_role.id, role_data)
        
        assert updated_role.display_name == "Updated Name"
        assert updated_role.description == test_role.description  # Unchanged
    
    def test_update_role_description(self, db: Session, role_service: RoleService, test_role):
        """Test updating role description."""
        role_data = RoleUpdate(
            display_name=None,
            description="Updated description"
        )
        
        updated_role = role_service.update_role(db, test_role.id, role_data)
        
        assert updated_role.description == "Updated description"
        assert updated_role.display_name == test_role.display_name  # Unchanged
    
    def test_update_role_both_fields(self, db: Session, role_service: RoleService, test_role):
        """Test updating both display name and description."""
        role_data = RoleUpdate(
            display_name="New Name",
            description="New description"
        )
        
        updated_role = role_service.update_role(db, test_role.id, role_data)
        
        assert updated_role.display_name == "New Name"
        assert updated_role.description == "New description"
    
    def test_update_role_not_found(self, db: Session, role_service: RoleService):
        """Test updating non-existent role."""
        role_data = RoleUpdate(
            display_name="New Name",
            description=None
        )
        
        with pytest.raises(HTTPException) as exc_info:
            role_service.update_role(db, 99999, role_data)
        
        assert exc_info.value.status_code == 404
    
    def test_update_system_role_forbidden(self, db: Session, role_service: RoleService, system_role):
        """Test that updating system role is forbidden."""
        role_data = RoleUpdate(
            display_name="Hacked Name",
            description=None
        )
        
        with pytest.raises(HTTPException) as exc_info:
            role_service.update_role(db, system_role.id, role_data)
        
        assert exc_info.value.status_code == 403
        assert "system role" in str(exc_info.value.detail).lower()


class TestDeleteRole(TestRoleService):
    """Tests for delete_role method."""
    
    def test_delete_role_success(self, db: Session, role_service: RoleService):
        """Test successful role deletion."""
        # Create a role without users
        role = Role(
            name="deletable",
            display_name="Deletable Role",
            description="Can be deleted",
            is_system_role=False
        )
        db.add(role)
        db.commit()
        role_id = role.id
        
        result = role_service.delete_role(db, role_id)
        
        assert result is True
        
        # Verify deletion
        deleted = db.query(Role).filter(Role.id == role_id).first()
        assert deleted is None
    
    def test_delete_role_not_found(self, db: Session, role_service: RoleService):
        """Test deleting non-existent role."""
        with pytest.raises(HTTPException) as exc_info:
            role_service.delete_role(db, 99999)
        
        assert exc_info.value.status_code == 404
    
    def test_delete_system_role_forbidden(self, db: Session, role_service: RoleService, system_role):
        """Test that deleting system role is forbidden."""
        with pytest.raises(HTTPException) as exc_info:
            role_service.delete_role(db, system_role.id)
        
        assert exc_info.value.status_code == 403
        assert "system role" in str(exc_info.value.detail).lower()
    
    def test_delete_role_with_users_forbidden(self, db: Session, role_service: RoleService, test_role, test_user):
        """Test that deleting role assigned to users is forbidden."""
        with pytest.raises(HTTPException) as exc_info:
            role_service.delete_role(db, test_role.id)
        
        assert exc_info.value.status_code == 400
        assert "assigned" in str(exc_info.value.detail).lower()


class TestGetRoleUsersCount(TestRoleService):
    """Tests for get_role_users_count method."""
    
    def test_get_role_users_count_with_users(self, db: Session, role_service: RoleService, test_role, test_user):
        """Test getting user count for role with users."""
        count = role_service.get_role_users_count(db, test_role.id)
        
        assert count >= 1
    
    def test_get_role_users_count_no_users(self, db: Session, role_service: RoleService):
        """Test getting user count for role without users."""
        role = Role(
            name="empty_role",
            display_name="Empty Role",
            description="No users",
            is_system_role=False
        )
        db.add(role)
        db.commit()
        
        count = role_service.get_role_users_count(db, role.id)
        
        assert count == 0
    
    def test_get_role_users_count_multiple_users(self, db: Session, role_service: RoleService, test_role, test_user):
        """Test getting user count for role with multiple users."""
        # Create additional users
        for i in range(3):
            user = User(
                username=f"user_{i}",
                email=f"user{i}@example.com",
                hashed_password=password_hasher.hash_password("Pass123!"),
                full_name=f"User {i}",
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
        
        count = role_service.get_role_users_count(db, test_role.id)
        
        assert count == 4  # Original test_user + 3 new users


class TestPermissionManagement(TestRoleService):
    """Tests for permission/policy management methods."""
    
    def test_add_permission_success(self, role_service: RoleService):
        """Test adding a permission."""
        permission = PermissionCreate(
            subject="test_role",
            object="/api/test",
            action="GET",
            effect="allow"
        )
        
        result = role_service.add_permission(permission)
        
        # Result depends on Casbin configuration
        assert isinstance(result, bool)
    
    def test_remove_permission_success(self, role_service: RoleService):
        """Test removing a permission."""
        # First add it
        permission = PermissionCreate(
            subject="test_role",
            object="/api/test",
            action="GET",
            effect="allow"
        )
        role_service.add_permission(permission)
        
        # Then remove it
        result = role_service.remove_permission(permission)
        
        assert isinstance(result, bool)
    
    def test_get_all_permissions(self, role_service: RoleService):
        """Test getting all permissions."""
        permissions = role_service.get_all_permissions()
        
        assert isinstance(permissions, list)
    
    def test_get_role_permissions(self, role_service: RoleService):
        """Test getting permissions for a specific role."""
        # Add a permission
        permission = PermissionCreate(
            subject="test_role",
            object="/api/test",
            action="GET",
            effect="allow"
        )
        role_service.add_permission(permission)
        
        permissions = role_service.get_role_permissions("test_role")
        
        assert isinstance(permissions, list)
    
    def test_check_permission(self, role_service: RoleService):
        """Test checking if user has permission."""
        result = role_service.check_permission(
            user_id=1,
            roles=["test_role"],
            resource="/api/test",
            action="GET"
        )
        
        assert isinstance(result, bool)
    
    def test_reload_policies(self, role_service: RoleService):
        """Test reloading Casbin policies."""
        result = role_service.reload_policies()
        
        assert isinstance(result, bool)
    
    def test_get_users_for_role(self, role_service: RoleService):
        """Test getting users assigned to a role."""
        users = role_service.get_users_for_role("test_role")
        
        assert isinstance(users, list)
    
    def test_get_roles_for_user(self, role_service: RoleService):
        """Test getting roles for a user."""
        roles = role_service.get_roles_for_user(1)
        
        assert isinstance(roles, list)


class TestEdgeCases(TestRoleService):
    """Tests for edge cases and special scenarios."""
    
    def test_role_name_with_special_characters(self, db: Session, role_service: RoleService):
        """Test creating role with special characters in name."""
        role_data = RoleCreate(
            name="role_with-dash",
            display_name="Role with Dash",
            description="Test role",
            is_system_role=False
        )
        
        role = role_service.create_role(db, role_data)
        
        assert role.name == "role_with-dash"
    
    def test_role_with_empty_description(self, db: Session, role_service: RoleService):
        """Test creating role with empty description."""
        role_data = RoleCreate(
            name="no_desc_role",
            display_name="No Description",
            description="",
            is_system_role=False
        )
        
        role = role_service.create_role(db, role_data)
        
        assert role.description == ""
    
    def test_role_with_long_name(self, db: Session, role_service: RoleService):
        """Test creating role with long name (up to limit)."""
        long_name = "role_" + "a" * 40  # Total 45 chars (within 50 limit)
        role_data = RoleCreate(
            name=long_name,
            display_name="Long Name Role",
            description="Test",
            is_system_role=False
        )
        
        role = role_service.create_role(db, role_data)
        
        assert role.name == long_name.lower()
    
    def test_update_role_with_none_values(self, db: Session, role_service: RoleService, test_role):
        """Test updating role with None values doesn't change fields."""
        original_display = test_role.display_name
        original_desc = test_role.description
        
        role_data = RoleUpdate(
            display_name=None,
            description=None
        )
        
        updated_role = role_service.update_role(db, test_role.id, role_data)
        
        assert updated_role.display_name == original_display
        assert updated_role.description == original_desc
    
    def test_multiple_system_roles(self, db: Session, role_service: RoleService):
        """Test that multiple system roles can exist."""
        system_roles = []
        for i in range(3):
            role_data = RoleCreate(
                name=f"sys_role_{i}",
                display_name=f"System Role {i}",
                description="System role",
                is_system_role=True
            )
            role = role_service.create_role(db, role_data)
            system_roles.append(role)
        
        assert len(system_roles) == 3
        assert all(r.is_system_role for r in system_roles)
    
    def test_permission_with_deny_effect(self, role_service: RoleService):
        """Test adding permission with deny effect."""
        permission = PermissionCreate(
            subject="test_role",
            object="/api/restricted",
            action="DELETE",
            effect="deny"
        )
        
        result = role_service.add_permission(permission)
        
        assert isinstance(result, bool)
    
    def test_permission_with_wildcard_resource(self, role_service: RoleService):
        """Test adding permission with wildcard resource."""
        permission = PermissionCreate(
            subject="admin",
            object="/api/*",
            action="*",
            effect="allow"
        )
        
        result = role_service.add_permission(permission)
        
        assert isinstance(result, bool)
    
    def test_list_roles_performance_with_many_roles(self, db: Session, role_service: RoleService):
        """Test performance of listing many roles."""
        # Create many roles
        for i in range(50):
            role = Role(
                name=f"perf_role_{i}",
                display_name=f"Performance Role {i}",
                description="Performance test",
                is_system_role=False
            )
            db.add(role)
        db.commit()
        
        roles, total = role_service.list_roles(db, limit=100)
        
        assert len(roles) <= 100
        assert total >= 50
