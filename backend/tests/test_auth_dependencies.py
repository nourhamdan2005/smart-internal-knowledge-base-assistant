from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core import security
from app.dependencies import auth
from app.schemas.user import UserRole


def make_user(role=UserRole.EMPLOYEE, active=True):
    now = datetime.now(timezone.utc)
    return {
        "id": "64b7f11a8b1234567890abcd",
        "email": "user@company.com",
        "full_name": "Company User",
        "hashed_password": "private",
        "role": role,
        "is_active": active,
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
    }


def credentials(token):
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


def configure_auth(monkeypatch):
    monkeypatch.setattr(auth.settings, "auth_enabled", True)
    monkeypatch.setattr(
        security.settings,
        "jwt_secret_key",
        "test-secret-that-is-long-and-random-enough",
    )


@pytest.mark.asyncio
async def test_missing_bearer_token_returns_401(monkeypatch):
    configure_auth(monkeypatch)

    with pytest.raises(HTTPException) as exc_info:
        await auth.get_current_user(None)

    assert exc_info.value.status_code == 401
    assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_invalid_and_expired_tokens_return_401(monkeypatch):
    configure_auth(monkeypatch)
    expired = security.create_access_token(
        "64b7f11a8b1234567890abcd",
        UserRole.EMPLOYEE,
        expiration=timedelta(seconds=-1),
    )

    for token in ["invalid", expired]:
        with pytest.raises(HTTPException) as exc_info:
            await auth.get_current_user(credentials(token))

        assert exc_info.value.status_code == 401


@pytest.mark.parametrize("database_user", [None, make_user(active=False)])
@pytest.mark.asyncio
async def test_deleted_or_inactive_user_token_is_rejected(
    monkeypatch,
    database_user,
):
    configure_auth(monkeypatch)
    token = security.create_access_token(
        "64b7f11a8b1234567890abcd",
        UserRole.EMPLOYEE,
    )

    async def get_user(user_id):
        return database_user

    monkeypatch.setattr(
        auth.user_repository,
        "get_by_id",
        get_user,
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth.get_current_user(credentials(token))

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_current_role_is_loaded_from_database(monkeypatch):
    configure_auth(monkeypatch)
    token = security.create_access_token(
        "64b7f11a8b1234567890abcd",
        UserRole.ADMIN,
    )

    async def get_user(user_id):
        return make_user(role=UserRole.EMPLOYEE)

    monkeypatch.setattr(
        auth.user_repository,
        "get_by_id",
        get_user,
    )

    current_user = await auth.get_current_user(
        credentials(token)
    )
    admin_dependency = auth.require_roles(UserRole.ADMIN)

    with pytest.raises(HTTPException) as exc_info:
        await admin_dependency(current_user)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_role_permissions_are_enforced():
    employee = make_user(UserRole.EMPLOYEE)
    editor = make_user(UserRole.EDITOR)
    admin = make_user(UserRole.ADMIN)

    authenticated = auth.require_roles(
        UserRole.ADMIN,
        UserRole.EDITOR,
        UserRole.EMPLOYEE,
    )
    editors = auth.require_roles(
        UserRole.ADMIN,
        UserRole.EDITOR,
    )
    admins = auth.require_roles(UserRole.ADMIN)

    assert await authenticated(employee) == employee
    assert await editors(editor) == editor
    assert await admins(admin) == admin

    with pytest.raises(HTTPException) as employee_denied:
        await editors(employee)

    with pytest.raises(HTTPException) as editor_denied:
        await admins(editor)

    assert employee_denied.value.status_code == 403
    assert editor_denied.value.status_code == 403


@pytest.mark.asyncio
async def test_disabled_auth_uses_explicit_development_principal(
    monkeypatch,
):
    monkeypatch.setattr(auth.settings, "auth_enabled", False)

    user = await auth.get_current_user(None)

    assert user["role"] == UserRole.ADMIN
    assert user["email"] == "development@local.invalid"
