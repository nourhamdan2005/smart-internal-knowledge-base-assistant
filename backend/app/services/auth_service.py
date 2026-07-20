import logging
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.repositories import user_repository
from app.schemas.user import UserCreate, UserRole, UserUpdate


logger = logging.getLogger(__name__)


class InvalidCredentialsError(RuntimeError):
    """Raised for all failed login attempts."""


class InactiveUserError(RuntimeError):
    """Raised when an inactive account attempts authentication."""


class UserNotFoundError(RuntimeError):
    """Raised when a requested user does not exist."""


class UserOperationForbiddenError(RuntimeError):
    """Raised when a user-management safety rule is violated."""


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    """Remove private credential fields from a service user."""
    return {
        key: value
        for key, value in user.items()
        if key != "hashed_password"
    }


async def create_user(
    user_data: UserCreate,
) -> dict[str, Any]:
    """Create an account with a securely hashed password."""
    user = await user_repository.create_user(
        email=str(user_data.email),
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
    )

    return public_user(user)


async def authenticate_user(
    email: str,
    password: str,
) -> dict[str, Any]:
    """Authenticate without revealing whether an email exists."""
    user = await user_repository.get_by_email(email)

    if user is None or not verify_password(
        password,
        user["hashed_password"],
    ):
        raise InvalidCredentialsError(
            "Invalid email or password"
        )

    if not user["is_active"]:
        raise InvalidCredentialsError(
            "Invalid email or password"
        )

    await user_repository.update_last_login(user["id"])

    return user


async def login(
    email: str,
    password: str,
) -> dict[str, Any]:
    user = await authenticate_user(email, password)
    token = create_access_token(
        subject=user["id"],
        role=user["role"],
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": (
            settings.jwt_access_token_expire_minutes * 60
        ),
    }


async def get_user(user_id: str) -> dict[str, Any]:
    user = await user_repository.get_by_id(user_id)

    if user is None:
        raise UserNotFoundError("User not found")

    return public_user(user)


async def list_users(
    page: int = 1,
    limit: int = 10,
) -> list[dict[str, Any]]:
    users = await user_repository.list_users(
        page=page,
        limit=limit,
    )
    return [public_user(user) for user in users]


async def update_user(
    user_id: str,
    user_data: UserUpdate,
    acting_user_id: str,
) -> dict[str, Any]:
    existing_user = await user_repository.get_by_id(user_id)

    if existing_user is None:
        raise UserNotFoundError("User not found")

    update_data = user_data.model_dump(exclude_unset=True)

    if (
        user_id == acting_user_id
        and update_data.get("is_active") is False
    ):
        raise UserOperationForbiddenError(
            "Administrators cannot deactivate themselves."
        )

    removes_active_admin = (
        existing_user["role"] == UserRole.ADMIN
        and existing_user["is_active"]
        and (
            update_data.get("is_active") is False
            or (
                "role" in update_data
                and update_data["role"] != UserRole.ADMIN
            )
        )
    )

    if (
        removes_active_admin
        and await user_repository.count_active_admins() <= 1
    ):
        raise UserOperationForbiddenError(
            "The final active administrator cannot be removed."
        )

    password = update_data.pop("password", None)

    if password is not None:
        update_data["hashed_password"] = hash_password(password)

    updated_user = await user_repository.update_user(
        user_id,
        update_data,
    )

    if updated_user is None:
        raise UserNotFoundError("User not found")

    return public_user(updated_user)


async def deactivate_user(
    user_id: str,
    acting_user_id: str,
) -> None:
    await update_user(
        user_id,
        UserUpdate(is_active=False),
        acting_user_id,
    )


async def bootstrap_admin() -> bool:
    """Idempotently create the configured first administrator."""
    if not settings.auth_enabled:
        logger.info(
            "Authentication is disabled; skipping bootstrap "
            "administrator."
        )
        return False

    email = settings.bootstrap_admin_email
    password = settings.bootstrap_admin_password

    if not email or not password:
        logger.info(
            "Bootstrap administrator configuration is incomplete; "
            "skipping."
        )
        return False

    existing_user = await user_repository.get_by_email(email)

    if existing_user is not None:
        logger.info(
            "Bootstrap administrator already exists; skipping."
        )
        return False

    await create_user(
        UserCreate(
            email=email,
            full_name=settings.bootstrap_admin_full_name,
            password=password,
            role=UserRole.ADMIN,
        )
    )
    logger.info("Bootstrap administrator created successfully.")
    return True


def development_principal() -> dict[str, Any]:
    """Return the explicit principal used when auth is disabled."""
    now = datetime.now(timezone.utc)
    return {
        "id": "development-user",
        "email": "development@local.invalid",
        "full_name": "Local Development Administrator",
        "role": UserRole.ADMIN,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
    }
