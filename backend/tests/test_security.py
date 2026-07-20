from datetime import timedelta

import jwt
import pytest

from app.core import security
from app.schemas.user import UserRole


def configure_secret(monkeypatch):
    monkeypatch.setattr(
        security.settings,
        "jwt_secret_key",
        "test-secret-that-is-long-and-random-enough",
    )


def test_password_hash_is_not_plaintext():
    hashed = security.hash_password("correct horse battery staple")

    assert hashed != "correct horse battery staple"
    assert hashed.startswith("$argon2")


def test_password_verification_accepts_correct_password():
    hashed = security.hash_password("correct horse battery staple")

    assert security.verify_password(
        "correct horse battery staple",
        hashed,
    )


def test_password_verification_rejects_wrong_password():
    hashed = security.hash_password("correct horse battery staple")

    assert not security.verify_password("wrong password", hashed)


def test_valid_access_token_decodes(monkeypatch):
    configure_secret(monkeypatch)

    token = security.create_access_token(
        "user-1",
        UserRole.EDITOR,
    )
    payload = security.decode_access_token(token)

    assert payload["sub"] == "user-1"
    assert payload["role"] == "editor"
    assert payload["type"] == "access"


def test_expired_access_token_is_rejected(monkeypatch):
    configure_secret(monkeypatch)
    token = security.create_access_token(
        "user-1",
        UserRole.EMPLOYEE,
        expiration=timedelta(seconds=-1),
    )

    with pytest.raises(security.AuthenticationError):
        security.decode_access_token(token)


def test_malformed_access_token_is_rejected(monkeypatch):
    configure_secret(monkeypatch)

    with pytest.raises(security.AuthenticationError):
        security.decode_access_token("not-a-jwt")


def test_wrong_token_type_is_rejected(monkeypatch):
    configure_secret(monkeypatch)
    token = jwt.encode(
        {
            "sub": "user-1",
            "type": "refresh",
        },
        security.settings.jwt_secret_key,
        algorithm=security.settings.jwt_algorithm,
    )

    with pytest.raises(security.AuthenticationError):
        security.decode_access_token(token)


def test_missing_subject_is_rejected(monkeypatch):
    configure_secret(monkeypatch)
    token = jwt.encode(
        {"type": "access"},
        security.settings.jwt_secret_key,
        algorithm=security.settings.jwt_algorithm,
    )

    with pytest.raises(security.AuthenticationError):
        security.decode_access_token(token)
