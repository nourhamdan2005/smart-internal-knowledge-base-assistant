from datetime import datetime, timezone

import pytest

from app.schemas.user import UserCreate, UserRole, UserUpdate
from app.services import auth_service


def make_user(
    role=UserRole.ADMIN,
    active=True,
    password="password123",
):
    now = datetime.now(timezone.utc)
    return {
        "id": "64b7f11a8b1234567890abcd",
        "email": "admin@company.com",
        "full_name": "Admin User",
        "hashed_password": auth_service.hash_password(password),
        "role": role,
        "is_active": active,
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
    }


@pytest.mark.asyncio
async def test_correct_credentials_produce_token(monkeypatch):
    user = make_user()
    updated = []

    async def get_user(email):
        return user

    async def update_login(user_id):
        updated.append(user_id)
        return True

    monkeypatch.setattr(
        auth_service.user_repository,
        "get_by_email",
        get_user,
    )
    monkeypatch.setattr(
        auth_service.user_repository,
        "update_last_login",
        update_login,
    )
    monkeypatch.setattr(
        auth_service.settings,
        "jwt_secret_key",
        "test-secret-that-is-long-and-random-enough",
    )

    result = await auth_service.login(
        "ADMIN@COMPANY.COM",
        "password123",
    )

    assert result["token_type"] == "bearer"
    assert result["access_token"]
    assert updated == [user["id"]]


@pytest.mark.parametrize("known_user", [True, False])
@pytest.mark.asyncio
async def test_invalid_login_uses_generic_error(
    monkeypatch,
    known_user,
):
    async def get_user(email):
        return make_user() if known_user else None

    monkeypatch.setattr(
        auth_service.user_repository,
        "get_by_email",
        get_user,
    )

    with pytest.raises(
        auth_service.InvalidCredentialsError,
        match="Invalid email or password",
    ):
        await auth_service.authenticate_user(
            "admin@company.com",
            "wrong-password",
        )


@pytest.mark.asyncio
async def test_inactive_user_cannot_log_in(monkeypatch):
    async def get_user(email):
        return make_user(active=False)

    monkeypatch.setattr(
        auth_service.user_repository,
        "get_by_email",
        get_user,
    )

    with pytest.raises(auth_service.InvalidCredentialsError):
        await auth_service.authenticate_user(
            "admin@company.com",
            "password123",
        )


@pytest.mark.asyncio
async def test_create_user_hashes_password(monkeypatch):
    captured = {}

    async def create_user(**kwargs):
        captured.update(kwargs)
        return {
            **make_user(role=kwargs["role"]),
            "email": kwargs["email"],
            "full_name": kwargs["full_name"],
            "hashed_password": kwargs["hashed_password"],
        }

    monkeypatch.setattr(
        auth_service.user_repository,
        "create_user",
        create_user,
    )

    result = await auth_service.create_user(
        UserCreate(
            email="Employee@Company.com",
            full_name="Employee User",
            password="password123",
            role=UserRole.EMPLOYEE,
        )
    )

    assert captured["email"] == "employee@company.com"
    assert captured["hashed_password"] != "password123"
    assert "hashed_password" not in result


@pytest.mark.asyncio
async def test_password_update_is_rehashed(monkeypatch):
    existing = make_user(role=UserRole.EMPLOYEE)
    captured = {}

    async def get_user(user_id):
        return existing

    async def update_user(user_id, update_data):
        captured.update(update_data)
        return {**existing, **update_data}

    monkeypatch.setattr(
        auth_service.user_repository,
        "get_by_id",
        get_user,
    )
    monkeypatch.setattr(
        auth_service.user_repository,
        "update_user",
        update_user,
    )

    await auth_service.update_user(
        existing["id"],
        UserUpdate(password="new-password123"),
        acting_user_id="different-admin",
    )

    assert "password" not in captured
    assert auth_service.verify_password(
        "new-password123",
        captured["hashed_password"],
    )


@pytest.mark.asyncio
async def test_admin_cannot_deactivate_self(monkeypatch):
    existing = make_user()

    async def get_user(user_id):
        return existing

    monkeypatch.setattr(
        auth_service.user_repository,
        "get_by_id",
        get_user,
    )

    with pytest.raises(
        auth_service.UserOperationForbiddenError,
    ):
        await auth_service.deactivate_user(
            existing["id"],
            acting_user_id=existing["id"],
        )


@pytest.mark.asyncio
async def test_final_active_admin_cannot_be_removed(monkeypatch):
    existing = make_user()

    async def get_user(user_id):
        return existing

    async def count_admins():
        return 1

    monkeypatch.setattr(
        auth_service.user_repository,
        "get_by_id",
        get_user,
    )
    monkeypatch.setattr(
        auth_service.user_repository,
        "count_active_admins",
        count_admins,
    )

    with pytest.raises(
        auth_service.UserOperationForbiddenError,
    ):
        await auth_service.update_user(
            existing["id"],
            UserUpdate(role=UserRole.EDITOR),
            acting_user_id="different-admin",
        )


@pytest.mark.asyncio
async def test_admin_can_deactivate_another_user(monkeypatch):
    existing = make_user(role=UserRole.EMPLOYEE)
    captured = {}

    async def get_user(user_id):
        return existing

    async def update_user(user_id, update_data):
        captured.update(update_data)
        return {**existing, **update_data}

    monkeypatch.setattr(
        auth_service.user_repository,
        "get_by_id",
        get_user,
    )
    monkeypatch.setattr(
        auth_service.user_repository,
        "update_user",
        update_user,
    )

    await auth_service.deactivate_user(
        existing["id"],
        acting_user_id="different-admin",
    )

    assert captured["is_active"] is False
