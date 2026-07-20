import pytest
from pydantic import ValidationError

from app.core.config import Settings


def make_settings(**values):
    return Settings(_env_file=None, **values)


def test_auth_settings_have_secure_defaults():
    configuration = make_settings()

    assert configuration.auth_enabled is True
    assert configuration.jwt_secret_key is None
    assert configuration.jwt_algorithm == "HS256"
    assert configuration.jwt_access_token_expire_minutes == 60


def test_empty_bootstrap_values_normalize_to_none():
    configuration = make_settings(
        bootstrap_admin_email=" ",
        bootstrap_admin_password="",
    )

    assert configuration.bootstrap_admin_email is None
    assert configuration.bootstrap_admin_password is None


def test_invalid_token_expiration_is_rejected():
    with pytest.raises(ValidationError):
        make_settings(jwt_access_token_expire_minutes=0)


def test_short_jwt_secret_is_rejected():
    with pytest.raises(ValidationError):
        make_settings(jwt_secret_key="too-short")
