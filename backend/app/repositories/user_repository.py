from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.core.database import database
from app.schemas.user import UserRole


collection = database["users"]


class UserRepositoryError(RuntimeError):
    """Base error for controlled user persistence failures."""


class DuplicateUserEmailError(UserRepositoryError):
    """Raised when a normalized email is already registered."""


def normalize_email(email: str) -> str:
    return email.strip().lower()


def user_helper(user: dict[str, Any]) -> dict[str, Any]:
    """Convert a MongoDB user into an internal service dictionary."""
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "full_name": user["full_name"],
        "hashed_password": user["hashed_password"],
        "role": UserRole(user["role"]),
        "is_active": user.get("is_active", True),
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
        "last_login_at": user.get("last_login_at"),
    }


async def ensure_indexes() -> list[str]:
    """Create the unique normalized-email index idempotently."""
    try:
        index_name = await collection.create_index(
            [("email", ASCENDING)],
            name="users_email_unique_idx",
            unique=True,
        )
    except PyMongoError as exc:
        raise UserRepositoryError(
            "User index initialization failed."
        ) from exc

    return [index_name]


async def create_user(
    email: str,
    full_name: str,
    hashed_password: str,
    role: UserRole,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    user_document = {
        "email": normalize_email(email),
        "full_name": full_name.strip(),
        "hashed_password": hashed_password,
        "role": role.value,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
    }

    try:
        result = await collection.insert_one(user_document)
        user_document["_id"] = result.inserted_id
    except DuplicateKeyError as exc:
        raise DuplicateUserEmailError(
            "A user with this email already exists."
        ) from exc
    except PyMongoError as exc:
        raise UserRepositoryError(
            "User creation failed."
        ) from exc

    return user_helper(user_document)


async def get_by_id(user_id: str) -> dict[str, Any] | None:
    if not ObjectId.is_valid(user_id):
        return None

    try:
        user = await collection.find_one(
            {"_id": ObjectId(user_id)}
        )
    except PyMongoError as exc:
        raise UserRepositoryError(
            "User lookup failed."
        ) from exc

    return user_helper(user) if user is not None else None


async def get_by_email(email: str) -> dict[str, Any] | None:
    try:
        user = await collection.find_one(
            {"email": normalize_email(email)}
        )
    except PyMongoError as exc:
        raise UserRepositoryError(
            "User lookup failed."
        ) from exc

    return user_helper(user) if user is not None else None


async def list_users(
    page: int = 1,
    limit: int = 10,
) -> list[dict[str, Any]]:
    cursor = (
        collection.find({})
        .sort("created_at", -1)
        .skip((page - 1) * limit)
        .limit(limit)
    )
    users: list[dict[str, Any]] = []

    try:
        async for user in cursor:
            users.append(user_helper(user))
    except PyMongoError as exc:
        raise UserRepositoryError(
            "User listing failed."
        ) from exc

    return users


async def update_user(
    user_id: str,
    update_data: dict[str, Any],
) -> dict[str, Any] | None:
    if not ObjectId.is_valid(user_id):
        return None

    normalized_update = {
        key: value.value if isinstance(value, UserRole) else value
        for key, value in update_data.items()
    }

    if "email" in normalized_update:
        normalized_update["email"] = normalize_email(
            normalized_update["email"]
        )

    normalized_update["updated_at"] = datetime.now(timezone.utc)

    try:
        user = await collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": normalized_update},
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError as exc:
        raise DuplicateUserEmailError(
            "A user with this email already exists."
        ) from exc
    except PyMongoError as exc:
        raise UserRepositoryError(
            "User update failed."
        ) from exc

    return user_helper(user) if user is not None else None


async def deactivate_user(user_id: str) -> bool:
    updated = await update_user(
        user_id,
        {"is_active": False},
    )
    return updated is not None


async def update_last_login(user_id: str) -> bool:
    if not ObjectId.is_valid(user_id):
        return False

    now = datetime.now(timezone.utc)
    try:
        result = await collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "last_login_at": now,
                    "updated_at": now,
                }
            },
        )
    except PyMongoError as exc:
        raise UserRepositoryError(
            "Last-login update failed."
        ) from exc

    return result.matched_count > 0


async def count_active_admins() -> int:
    try:
        return await collection.count_documents(
            {
                "role": UserRole.ADMIN.value,
                "is_active": True,
            }
        )
    except PyMongoError as exc:
        raise UserRepositoryError(
            "Administrator count failed."
        ) from exc
