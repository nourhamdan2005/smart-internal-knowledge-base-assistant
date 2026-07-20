import logging

import pytest

from app.services import auth_service


@pytest.mark.asyncio
async def test_bootstrap_creates_first_admin(monkeypatch, caplog):
    created = []

    async def get_user(email):
        return None

    async def create_user(user_data):
        created.append(user_data)
        return {}

    monkeypatch.setattr(auth_service.settings, "auth_enabled", True)
    monkeypatch.setattr(
        auth_service.settings,
        "bootstrap_admin_email",
        "admin@company.com",
    )
    monkeypatch.setattr(
        auth_service.settings,
        "bootstrap_admin_password",
        "super-secret-password",
    )
    monkeypatch.setattr(
        auth_service.user_repository,
        "get_by_email",
        get_user,
    )
    monkeypatch.setattr(auth_service, "create_user", create_user)

    with caplog.at_level(logging.INFO):
        assert await auth_service.bootstrap_admin() is True

    assert created[0].role.value == "admin"
    assert "super-secret-password" not in caplog.text


@pytest.mark.asyncio
async def test_bootstrap_skips_existing_user(monkeypatch):
    async def get_user(email):
        return {"id": "existing"}

    monkeypatch.setattr(auth_service.settings, "auth_enabled", True)
    monkeypatch.setattr(
        auth_service.settings,
        "bootstrap_admin_email",
        "admin@company.com",
    )
    monkeypatch.setattr(
        auth_service.settings,
        "bootstrap_admin_password",
        "super-secret-password",
    )
    monkeypatch.setattr(
        auth_service.user_repository,
        "get_by_email",
        get_user,
    )

    assert await auth_service.bootstrap_admin() is False


@pytest.mark.asyncio
async def test_bootstrap_skips_incomplete_configuration(monkeypatch):
    monkeypatch.setattr(auth_service.settings, "auth_enabled", True)
    monkeypatch.setattr(
        auth_service.settings,
        "bootstrap_admin_email",
        None,
    )
    monkeypatch.setattr(
        auth_service.settings,
        "bootstrap_admin_password",
        None,
    )

    assert await auth_service.bootstrap_admin() is False
