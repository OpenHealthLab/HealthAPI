"""
Comprehensive test cases for UserService.

Tests cover user CRUD operations, role assignment,
password management, and edge cases.
"""

import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.user_service import UserService
from app.models.user import User, Role, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserStats
from app.core.security import password_hasher


class TestUserService:
    """Test suite for UserService."""
    
    @pytest.fixture
    def user_service(self):
        """Create UserService instance."""
        return UserService()
    
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
    def admin_role(self, db: Session):
        """Get the admin role (already seeded by conftest)."""
        role = db.query(Role).filter(Role.name == "admin").first()
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


class TestCreateUser(TestUserService):
    """Tests for create_user method."""
    
    def test_create_user_success(self, db: Session, user_service: UserService, test_role):
        """Test successful user creation."""
        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            password="SecurePass123!",
            full_name="New User",
            is_active=True,
            is_superuser=False,
            roles=["test_role"]
        )
        
        user = user_service.create_user(db, user_data)
        
        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.is_active is True
        assert user.is_superuser is False
        assert "test_role" in user.roles
    
    def test_create_user_lowercase_username(self, db: Session, user_service: UserService):
        """Test that username is converted to lowercase."""
        user_data = UserCreate(
            username="NewUser",
            email="newuser@example.com",
            password="SecurePass123!",
            full_name="New User",
            is_active=True,
            is_superuser=False,
            roles=[]
        )
        
        user = user_service.create_user(db, user_data)
        
        assert user.username == "newuser"
    
    def test_create_user_duplicate_username(self, db: Session, user_service: UserService, test_user):
        """Test creating user with duplicate username fails."""
        user_data = UserCreate(
            username="testuser",
            email="different@example.com",
            password="SecurePass123!",
            full_name="Another User",
            is_active=True,
            is_superuser=False,
            roles=[]
        )
        
        with pytest.raises(HTTPException) as exc_info:
            user_service.create_user(db, user_data)
        
        assert exc_info.value.status_code == 400
        assert "Username already exists" in str(exc_info.value.detail)
    
    def test_create_user_duplicate_email(self, db: Session, user_service: UserService, test_user):
        """Test creating user with duplicate email fails."""
        user_data = UserCreate(
            username="differentuser",
            email="test@example.com",
            password="SecurePass123!",
            full_name="Another User",
            is_active=True,
            is_superuser=False,
            roles=[]
        )
        
        with pytest.raises(HTTPException) as exc_info:
            user_service.create_user(db, user_data)
        
        assert exc_info.value.status_code == 400
        assert "Email already exists" in str(exc_info.value.detail)
    
    def test_create_user_weak_password(self, db: Session, user_service: UserService):
        """Test creating user with weak password fails."""
        # Password is 8+ characters but lacks uppercase, digit, or special character
        # This should fail the password_strength validation
        with pytest.raises(ValueError) as exc_info:
            user_data = UserCreate(
                username="weakuser",
                email="weak@example.com",
                password="weakpass",
                full_name="Weak User",
                is_active=True,
                is_superuser=False,
                roles=[]
            )
        
        assert "uppercase" in str(exc_info.value).lower() or "digit" in str(exc_info.value).lower() or "special" in str(exc_info.value).lower()
    
    def test_create_user_with_multiple_roles(self, db: Session, user_service: UserService, test_role):
        """Test creating user with multiple roles."""
        # Create a second role for this test
        role2 = Role(
            name="editor_role",
            display_name="Editor",
            description="Editor role",
            is_system_role=False
        )
        db.add(role2)
        db.commit()
        
        user_data = UserCreate(
            username="multirole",
            email="multi@example.com",
            password="SecurePass123!",
            full_name="Multi Role User",
            is_active=True,
            is_superuser=False,
            roles=["test_role", "editor_role"]
        )
        
        user = user_service.create_user(db, user_data)
        
        assert len(user.roles) == 2
        assert "test_role" in user.roles
        assert "editor_role" in user.roles
    
    def test_create_superuser(self, db: Session, user_service: UserService):
        """Test creating a superuser."""
        user_data = UserCreate(
            username="superuser",
            email="super@example.com",
            password="SecurePass123!",
            full_name="Super User",
            is_active=True,
            is_superuser=True,
            roles=[]
        )
        
        user = user_service.create_user(db, user_data)
        
        assert user.is_superuser is True
    
    def test_create_inactive_user(self, db: Session, user_service: UserService):
        """Test creating an inactive user."""
        user_data = UserCreate(
            username="inactive",
            email="inactive@example.com",
            password="SecurePass123!",
            full_name="Inactive User",
            is_active=False,
            is_superuser=False,
            roles=[]
        )
        
        user = user_service.create_user(db, user_data)
        
        assert user.is_active is False


class TestGetUser(TestUserService):
    """Tests for get_user methods."""
    
    def test_get_user_by_id_success(self, db: Session, user_service: UserService, test_user):
        """Test successful user retrieval by ID."""
        user = user_service.get_user_by_id(db, test_user.id)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.username == test_user.username
    
    def test_get_user_by_id_not_found(self, db: Session, user_service: UserService):
        """Test retrieving non-existent user by ID."""
        user = user_service.get_user_by_id(db, 99999)
        
        assert user is None
    
    def test_get_user_by_username_success(self, db: Session, user_service: UserService, test_user):
        """Test successful user retrieval by username."""
        user = user_service.get_user_by_username(db, "testuser")
        
        assert user is not None
        assert user.username == "testuser"
    
    def test_get_user_by_username_case_insensitive(self, db: Session, user_service: UserService, test_user):
        """Test that username lookup is case-insensitive."""
        user = user_service.get_user_by_username(db, "TESTUSER")
        
        assert user is not None
        assert user.username == "testuser"
    
    def test_get_user_by_username_not_found(self, db: Session, user_service: UserService):
        """Test retrieving non-existent user by username."""
        user = user_service.get_user_by_username(db, "nonexistent")
        
        assert user is None
    
    def test_get_user_by_email_success(self, db: Session, user_service: UserService, test_user):
        """Test successful user retrieval by email."""
        user = user_service.get_user_by_email(db, "test@example.com")
        
        assert user is not None
        assert user.email == "test@example.com"
    
    def test_get_user_by_email_not_found(self, db: Session, user_service: UserService):
        """Test retrieving non-existent user by email."""
        user = user_service.get_user_by_email(db, "nonexistent@example.com")
        
        assert user is None


class TestListUsers(TestUserService):
    """Tests for list_users method."""
    
    def test_list_users_success(self, db: Session, user_service: UserService, test_user):
        """Test listing all users."""
        users, total = user_service.list_users(db)
        
        assert len(users) >= 1
        assert total >= 1
        assert any(u.id == test_user.id for u in users)
    
    def test_list_users_pagination(self, db: Session, user_service: UserService, test_role):
        """Test pagination of users."""
        # Create multiple users
        for i in range(10):
            user = User(
                username=f"user_{i}",
                email=f"user{i}@example.com",
                hashed_password=password_hasher.hash_password("Pass123!"),
                full_name=f"User {i}",
                is_active=True,
                oauth_provider="local"
            )
            db.add(user)
        db.commit()
        
        # Get first page
        page1, total1 = user_service.list_users(db, skip=0, limit=5)
        assert len(page1) == 5
        
        # Get second page
        page2, total2 = user_service.list_users(db, skip=5, limit=5)
        assert len(page2) == 5
        
        # Total should be the same
        assert total1 == total2
    
    def test_list_users_filter_active(self, db: Session, user_service: UserService):
        """Test filtering users by active status."""
        # Create active and inactive users
        for i in range(3):
            user = User(
                username=f"active_{i}",
                email=f"active{i}@example.com",
                hashed_password=password_hasher.hash_password("Pass123!"),
                full_name=f"Active {i}",
                is_active=True,
                oauth_provider="local"
            )
            db.add(user)
        
        for i in range(2):
            user = User(
                username=f"inactive_{i}",
                email=f"inactive{i}@example.com",
                hashed_password=password_hasher.hash_password("Pass123!"),
                full_name=f"Inactive {i}",
                is_active=False,
                oauth_provider="local"
            )
            db.add(user)
        db.commit()
        
        active_users, active_total = user_service.list_users(db, is_active=True)
        inactive_users, inactive_total = user_service.list_users(db, is_active=False)
        
        assert all(u.is_active for u in active_users)
        assert all(not u.is_active for u in inactive_users)


class TestUpdateUser(TestUserService):
    """Tests for update_user method."""
    
    def test_update_user_email(self, db: Session, user_service: UserService, test_user):
        """Test updating user email."""
        user_data = UserUpdate(
            email="newemail@example.com",
            full_name=None,
            is_active=None,
            is_superuser=None
        )
        
        updated_user = user_service.update_user(db, test_user.id, user_data)
        
        assert updated_user.email == "newemail@example.com"
    
    def test_update_user_full_name(self, db: Session, user_service: UserService, test_user):
        """Test updating user full name."""
        user_data = UserUpdate(
            email=None,
            full_name="Updated Name",
            is_active=None,
            is_superuser=None
        )
        
        updated_user = user_service.update_user(db, test_user.id, user_data)
        
        assert updated_user.full_name == "Updated Name"
    
    def test_update_user_is_active(self, db: Session, user_service: UserService, test_user):
        """Test updating user active status."""
        user_data = UserUpdate(
            email=None,
            full_name=None,
            is_active=False,
            is_superuser=None
        )
        
        updated_user = user_service.update_user(db, test_user.id, user_data)
        
        assert updated_user.is_active is False
    
    def test_update_user_is_superuser(self, db: Session, user_service: UserService, test_user):
        """Test updating user superuser status."""
        user_data = UserUpdate(
            email=None,
            full_name=None,
            is_active=None,
            is_superuser=True
        )
        
        updated_user = user_service.update_user(db, test_user.id, user_data)
        
        assert updated_user.is_superuser is True
    
    def test_update_user_not_found(self, db: Session, user_service: UserService):
        """Test updating non-existent user."""
        user_data = UserUpdate(
            email="new@example.com",
            full_name=None,
            is_active=None,
            is_superuser=None
        )
        
        with pytest.raises(HTTPException) as exc_info:
            user_service.update_user(db, 99999, user_data)
        
        assert exc_info.value.status_code == 404
    
    def test_update_user_duplicate_email(self, db: Session, user_service: UserService, test_user):
        """Test updating user with duplicate email fails."""
        # Create another user
        another_user = User(
            username="another",
            email="another@example.com",
            hashed_password=password_hasher.hash_password("Pass123!"),
            full_name="Another User",
            is_active=True,
            oauth_provider="local"
        )
        db.add(another_user)
        db.commit()
        
        # Try to update test_user with another_user's email
        user_data = UserUpdate(
            email="another@example.com",
            full_name=None,
            is_active=None,
            is_superuser=None
        )
        
        with pytest.raises(HTTPException) as exc_info:
            user_service.update_user(db, test_user.id, user_data)
        
        assert exc_info.value.status_code == 400
        assert "already in use" in str(exc_info.value.detail)


class TestDeleteUser(TestUserService):
    """Tests for delete_user method."""
    
    def test_delete_user_success(self, db: Session, user_service: UserService):
        """Test successful user deletion."""
        # Create a user to delete
        user = User(
            username="deletable",
            email="delete@example.com",
            hashed_password=password_hasher.hash_password("Pass123!"),
            full_name="Deletable User",
            is_active=True,
            oauth_provider="local"
        )
        db.add(user)
        db.commit()
        user_id = user.id
        
        result = user_service.delete_user(db, user_id)
        
        assert result is True
        
        # Verify deletion
        deleted = db.query(User).filter(User.id == user_id).first()
        assert deleted is None
    
    def test_delete_user_not_found(self, db: Session, user_service: UserService):
        """Test deleting non-existent user."""
        with pytest.raises(HTTPException) as exc_info:
            user_service.delete_user(db, 99999)
        
        assert exc_info.value.status_code == 404


class TestRoleAssignment(TestUserService):
    """Tests for assign_role and remove_role methods."""
    
    def test_assign_role_success(self, db: Session, user_service: UserService, test_user):
        """Test successful role assignment."""
        # Create a role for this test
        new_role = Role(
            name="assign_test_role",
            display_name="Assign Test",
            description="Test role for assignment",
            is_system_role=False
        )
        db.add(new_role)
        db.commit()
        
        result = user_service.assign_role(db, test_user.id, "assign_test_role")
        
        assert result is True
        
        # Verify assignment
        db.refresh(test_user)
        assert "assign_test_role" in test_user.roles
    
    def test_assign_role_user_not_found(self, db: Session, user_service: UserService):
        """Test assigning role to non-existent user."""
        with pytest.raises(HTTPException) as exc_info:
            user_service.assign_role(db, 99999, "admin")
        
        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)
    
    def test_assign_role_role_not_found(self, db: Session, user_service: UserService, test_user):
        """Test assigning non-existent role."""
        with pytest.raises(HTTPException) as exc_info:
            user_service.assign_role(db, test_user.id, "nonexistent")
        
        assert exc_info.value.status_code == 404
        assert "Role" in str(exc_info.value.detail)
    
    def test_assign_role_already_assigned(self, db: Session, user_service: UserService, test_user):
        """Test assigning role that user already has."""
        with pytest.raises(HTTPException) as exc_info:
            user_service.assign_role(db, test_user.id, "test_role")
        
        assert exc_info.value.status_code == 400
        assert "already has role" in str(exc_info.value.detail)
    
    def test_remove_role_success(self, db: Session, user_service: UserService, test_user):
        """Test successful role removal."""
        result = user_service.remove_role(db, test_user.id, "test_role")
        
        assert result is True
        
        # Verify removal
        db.refresh(test_user)
        assert "test_role" not in test_user.roles
    
    def test_remove_role_user_not_found(self, db: Session, user_service: UserService):
        """Test removing role from non-existent user."""
        with pytest.raises(HTTPException) as exc_info:
            user_service.remove_role(db, 99999, "test_role")
        
        assert exc_info.value.status_code == 404
    
    def test_remove_role_role_not_found(self, db: Session, user_service: UserService, test_user):
        """Test removing non-existent role."""
        with pytest.raises(HTTPException) as exc_info:
            user_service.remove_role(db, test_user.id, "nonexistent")
        
        assert exc_info.value.status_code == 404
    
    def test_remove_role_not_assigned(self, db: Session, user_service: UserService, test_user):
        """Test removing role that user doesn't have."""
        # Create a role that test_user doesn't have
        unassigned_role = Role(
            name="unassigned_role",
            display_name="Unassigned",
            description="Role not assigned to test user",
            is_system_role=False
        )
        db.add(unassigned_role)
        db.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            user_service.remove_role(db, test_user.id, "unassigned_role")
        
        assert exc_info.value.status_code == 400
        assert "does not have role" in str(exc_info.value.detail)


class TestGetUserRoles(TestUserService):
    """Tests for get_user_roles method."""
    
    def test_get_user_roles_success(self, db: Session, user_service: UserService, test_user):
        """Test getting user roles."""
        roles = user_service.get_user_roles(db, test_user.id)
        
        assert isinstance(roles, list)
        assert "test_role" in roles
    
    def test_get_user_roles_multiple(self, db: Session, user_service: UserService, test_user):
        """Test getting multiple roles for user."""
        # Create and assign another role
        second_role = Role(
            name="second_test_role",
            display_name="Second Test",
            description="Second role for user",
            is_system_role=False
        )
        db.add(second_role)
        db.commit()
        
        user_service.assign_role(db, test_user.id, "second_test_role")
        
        roles = user_service.get_user_roles(db, test_user.id)
        
        assert len(roles) == 2
        assert "test_role" in roles
        assert "second_test_role" in roles
    
    def test_get_user_roles_no_roles(self, db: Session, user_service: UserService):
        """Test getting roles for user without roles."""
        # Create user without roles
        user = User(
            username="noroles",
            email="noroles@example.com",
            hashed_password=password_hasher.hash_password("Pass123!"),
            full_name="No Roles User",
            is_active=True,
            oauth_provider="local"
        )
        db.add(user)
        db.commit()
        
        roles = user_service.get_user_roles(db, user.id)
        
        assert len(roles) == 0
    
    def test_get_user_roles_user_not_found(self, db: Session, user_service: UserService):
        """Test getting roles for non-existent user."""
        roles = user_service.get_user_roles(db, 99999)
        
        assert roles == []


class TestChangePassword(TestUserService):
    """Tests for change_password method."""
    
    def test_change_password_success(self, db: Session, user_service: UserService, test_user):
        """Test successful password change."""
        result = user_service.change_password(
            db, test_user.id,
            current_password="TestPassword123!",
            new_password="NewPassword123!"
        )
        
        assert result is True
        
        # Verify new password works
        db.refresh(test_user)
        assert password_hasher.verify_password("NewPassword123!", test_user.hashed_password)
    
    def test_change_password_user_not_found(self, db: Session, user_service: UserService):
        """Test changing password for non-existent user."""
        with pytest.raises(HTTPException) as exc_info:
            user_service.change_password(
                db, 99999,
                current_password="Old123!",
                new_password="New123!"
            )
        
        assert exc_info.value.status_code == 404
    
    def test_change_password_wrong_current(self, db: Session, user_service: UserService, test_user):
        """Test changing password with wrong current password."""
        with pytest.raises(HTTPException) as exc_info:
            user_service.change_password(
                db, test_user.id,
                current_password="WrongPassword123!",
                new_password="NewPassword123!"
            )
        
        assert exc_info.value.status_code == 401
        assert "Invalid current password" in str(exc_info.value.detail)
    
    def test_change_password_weak_new_password(self, db: Session, user_service: UserService, test_user):
        """Test changing to weak password fails."""
        with pytest.raises(HTTPException) as exc_info:
            user_service.change_password(
                db, test_user.id,
                current_password="TestPassword123!",
                new_password="weak"
            )
        
        assert exc_info.value.status_code == 400


class TestGetUserStats(TestUserService):
    """Tests for get_user_stats method."""
    
    def test_get_user_stats_success(self, db: Session, user_service: UserService, test_user):
        """Test getting user statistics."""
        stats = user_service.get_user_stats(db)
        
        assert isinstance(stats, UserStats)
        assert stats.total_users >= 1
        assert stats.active_users >= 0
        assert stats.inactive_users >= 0
        assert stats.users_with_2fa >= 0
        assert stats.oauth_users >= 0
    
    def test_get_user_stats_with_2fa_users(self, db: Session, user_service: UserService):
        """Test stats with 2FA enabled users."""
        # Create user with 2FA
        user = User(
            username="2fauser",
            email="2fa@example.com",
            hashed_password=password_hasher.hash_password("Pass123!"),
            full_name="2FA User",
            is_active=True,
            is_2fa_enabled=True,
            totp_secret="secret",
            oauth_provider="local"
        )
        db.add(user)
        db.commit()
        
        stats = user_service.get_user_stats(db)
        
        assert stats.users_with_2fa >= 1
    
    def test_get_user_stats_with_oauth_users(self, db: Session, user_service: UserService):
        """Test stats with OAuth users."""
        # Create OAuth user
        user = User(
            username="oauthuser",
            email="oauth@example.com",
            hashed_password=None,
            full_name="OAuth User",
            is_active=True,
            oauth_provider="google"
        )
        db.add(user)
        db.commit()
        
        stats = user_service.get_user_stats(db)
        
        assert stats.oauth_users >= 1


class TestEdgeCases(TestUserService):
    """Tests for edge cases and special scenarios."""
    
    def test_user_with_special_characters_in_username(self, db: Session, user_service: UserService):
        """Test creating user with special characters in username."""
        user_data = UserCreate(
            username="user_with-dash",
            email="special@example.com",
            password="SecurePass123!",
            full_name="Special User",
            is_active=True,
            is_superuser=False,
            roles=[]
        )
        
        user = user_service.create_user(db, user_data)
        
        assert user.username == "user_with-dash"
    
    def test_user_with_unicode_in_full_name(self, db: Session, user_service: UserService):
        """Test creating user with unicode characters in full name."""
        user_data = UserCreate(
            username="unicode",
            email="unicode@example.com",
            password="SecurePass123!",
            full_name="用户 名字",
            is_active=True,
            is_superuser=False,
            roles=[]
        )
        
        user = user_service.create_user(db, user_data)
        
        assert user.full_name == "用户 名字"
    
    def test_user_with_long_email(self, db: Session, user_service: UserService):
        """Test creating user with very long email."""
        long_email = "a" * 50 + "@example.com"
        user_data = UserCreate(
            username="longemail",
            email=long_email,
            password="SecurePass123!",
            full_name="Long Email User",
            is_active=True,
            is_superuser=False,
            roles=[]
        )
        
        user = user_service.create_user(db, user_data)
        
        assert user.email == long_email
    
    def test_update_user_with_none_values(self, db: Session, user_service: UserService, test_user):
        """Test updating user with None values doesn't change fields."""
        original_email = test_user.email
        original_name = test_user.full_name
        
        user_data = UserUpdate(
            email=None,
            full_name=None,
            is_active=None,
            is_superuser=None
        )
        
        updated_user = user_service.update_user(db, test_user.id, user_data)
        
        assert updated_user.email == original_email
        assert updated_user.full_name == original_name
    
    def test_assign_multiple_roles_sequentially(self, db: Session, user_service: UserService, test_user):
        """Test assigning multiple roles one by one."""
        # Create additional roles
        role1 = Role(
            name="sequential_role_1",
            display_name="Sequential 1",
            description="Sequential role 1",
            is_system_role=False
        )
        role2 = Role(
            name="sequential_role_2",
            display_name="Sequential 2",
            description="Sequential role 2",
            is_system_role=False
        )
        db.add_all([role1, role2])
        db.commit()
        
        # Assign roles
        user_service.assign_role(db, test_user.id, "sequential_role_1")
        user_service.assign_role(db, test_user.id, "sequential_role_2")
        
        roles = user_service.get_user_roles(db, test_user.id)
        
        assert len(roles) == 3
        assert "test_role" in roles
        assert "sequential_role_1" in roles
        assert "sequential_role_2" in roles
    
    def test_user_with_empty_full_name(self, db: Session, user_service: UserService):
        """Test creating user with empty full name."""
        user_data = UserCreate(
            username="noname",
            email="noname@example.com",
            password="SecurePass123!",
            full_name="",
            is_active=True,
            is_superuser=False,
            roles=[]
        )
        
        user = user_service.create_user(db, user_data)
        
        assert user.full_name == ""
    
    def test_list_users_large_dataset(self, db: Session, user_service: UserService):
        """Test performance with many users."""
        # Create many users
        for i in range(50):
            user = User(
                username=f"perf_user_{i}",
                email=f"perf{i}@example.com",
                hashed_password=password_hasher.hash_password("Pass123!"),
                full_name=f"Perf User {i}",
                is_active=True,
                oauth_provider="local"
            )
            db.add(user)
        db.commit()
        
        users, total = user_service.list_users(db, limit=100)
        
        assert len(users) <= 100
