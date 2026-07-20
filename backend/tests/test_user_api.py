from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import users
from app.repositories.user_repository import (
    DuplicateUserEmailError,
)
from app.schemas.user import UserCreate, UserRole, UserUpdate


def user_response():
    now = datetime.now(timezone.utc)
    return {
        "id": "64b7f11a8b1234567890abcd",
        "email": "employee@company.com",
        "full_name": "Employee User",
        "role": UserRole.EMPLOYEE,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
    }


@pytest.mark.asyncio
async def test_duplicate_user_email_returns_409(monkeypatch):
    async def create_user(user_data):
        raise DuplicateUserEmailError("duplicate")

    monkeypatch.setattr(
        users.auth_service,
        "create_user",
        create_user,
    )

    with pytest.raises(HTTPException) as exc_info:
        await users.create_user(
            UserCreate(
                email="employee@company.com",
                full_name="Employee User",
                password="password123",
            )
        )

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_admin_can_change_user_role(monkeypatch):
    result = {
        **user_response(),
        "role": UserRole.EDITOR,
    }

    async def update_user(**kwargs):
        assert kwargs["acting_user_id"] == "admin-id"
        assert kwargs["user_data"].role == UserRole.EDITOR
        return result

    monkeypatch.setattr(
        users.auth_service,
        "update_user",
        update_user,
    )

    response = await users.update_user(
        user_id=result["id"],
        user_data=UserUpdate(role=UserRole.EDITOR),
        current_user={"id": "admin-id"},
    )

    assert response.role == UserRole.EDITOR
