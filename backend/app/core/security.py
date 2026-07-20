from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings
from app.schemas.user import UserRole


password_hash = PasswordHash.recommended()


class AuthenticationError(RuntimeError):
    """Raised when credentials or access tokens are invalid."""


class SecurityConfigurationError(RuntimeError):
    """Raised when authentication security is not configured."""


def hash_password(password: str) -> str:
    """Hash a password using Argon2."""
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Safely verify a plaintext password against an Argon2 hash."""
    try:
        return password_hash.verify(
            plain_password,
            hashed_password,
        )
    except Exception:
        return False


def create_access_token(
    subject: str,
    role: UserRole | str,
    expiration: timedelta | None = None,
) -> str:
    """Create a signed bearer access token."""
    if not settings.jwt_secret_key:
        raise SecurityConfigurationError(
            "JWT authentication is not configured."
        )

    now = datetime.now(timezone.utc)
    expires_at = now + (
        expiration
        if expiration is not None
        else timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
    )
    payload = {
        "sub": subject,
        "role": str(role),
        "iat": now,
        "exp": expires_at,
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a bearer access token."""
    if not settings.jwt_secret_key:
        raise SecurityConfigurationError(
            "JWT authentication is not configured."
        )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={
                "require": [
                    "sub",
                    "role",
                    "iat",
                    "exp",
                    "type",
                ]
            },
        )
    except InvalidTokenError as exc:
        raise AuthenticationError(
            "Invalid or expired access token."
        ) from exc

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject:
        raise AuthenticationError(
            "Invalid or expired access token."
        )

    if payload.get("type") != "access":
        raise AuthenticationError(
            "Invalid or expired access token."
        )

    return payload
