import pytest
from app.schemas.user import UserUpdate, PasswordUpdate
from pydantic import ValidationError

def test_user_update_requires_at_least_one_field():
    # All fields None should raise a validation error
    with pytest.raises(ValidationError) as exc_info:
        UserUpdate()
    assert "At least one field must be updated" in str(exc_info.value)

def test_user_update_with_first_name_only():
    # Only first_name provided, should be valid
    update = UserUpdate(first_name="Alice")
    assert update.first_name == "Alice"

def test_user_update_with_last_name_only():
    # Only last_name provided, should be valid
    update = UserUpdate(last_name="Smith")
    assert update.last_name == "Smith"

def test_user_update_with_email_only():
    # Only email provided, should be valid
    update = UserUpdate(email="alice@example.com")
    assert update.email == "alice@example.com"

def test_user_update_with_username_only():
    # Only username provided, should be valid
    update = UserUpdate(username="aliceuser")
    assert update.username == "aliceuser"

def test_user_update_with_multiple_fields():
    # Multiple fields provided, should be valid
    update = UserUpdate(first_name="Alice", last_name="Smith")
    assert update.first_name == "Alice"
    assert update.last_name == "Smith"

def test_password_update_valid():
    # Should succeed when new_password and confirm_new_password match and are different from current_password
    data = {
        "current_password": "OldPass123!",
        "new_password": "NewPass456!",
        "confirm_new_password": "NewPass456!"
    }
    obj = PasswordUpdate(**data)
    assert obj.new_password == "NewPass456!"
    assert obj.confirm_new_password == "NewPass456!"
    assert obj.current_password == "OldPass123!"

def test_password_update_mismatched_confirmation():
    # Should raise ValidationError when new_password and confirm_new_password do not match
    data = {
        "current_password": "OldPass123!",
        "new_password": "NewPass456!",
        "confirm_new_password": "WrongPass456!"
    }
    with pytest.raises(ValidationError) as exc_info:
        PasswordUpdate(**data)
    assert "New password and confirmation do not match" in str(exc_info.value)

def test_password_update_same_as_current():
    # Should raise ValidationError when new_password is the same as current_password
    data = {
        "current_password": "OldPass123!",
        "new_password": "OldPass123!",
        "confirm_new_password": "OldPass123!"
    }
    with pytest.raises(ValidationError) as exc_info:
        PasswordUpdate(**data)
    assert "New password must be different from current password" in str(exc_info.value)