from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.repositories import user_repository
from app.schemas.user import UserRole


def mongo_user(
    email="user@company.com",
    role="employee",
    active=True,
):
    now = datetime.now(timezone.utc)
    return {
        "_id": ObjectId("64b7f11a8b1234567890abcd"),
        "email": email,
        "full_name": "Company User",
        "hashed_password": "hashed",
        "role": role,
        "is_active": active,
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
    }


class FakeCursor:
    def __init__(self, users):
        self.users = users

    def sort(self, *args):
        return self

    def skip(self, count):
        return self

    def limit(self, count):
        return self

    def __aiter__(self):
        self.iterator = iter(self.users)
        return self

    async def __anext__(self):
        try:
            return next(self.iterator)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class FakeCollection:
    def __init__(self):
        self.user = mongo_user()
        self.created_index = None
        self.insert_error = None

    async def create_index(self, keys, **kwargs):
        self.created_index = (keys, kwargs)
        return kwargs["name"]

    async def insert_one(self, document):
        if self.insert_error:
            raise self.insert_error

        self.user = {
            **document,
            "_id": ObjectId("64b7f11a8b1234567890abcd"),
        }
        return SimpleNamespace(inserted_id=self.user["_id"])

    async def find_one(self, query):
        if "email" in query:
            return (
                self.user
                if self.user["email"] == query["email"]
                else None
            )

        return self.user

    def find(self, query):
        return FakeCursor([self.user])

    async def find_one_and_update(
        self,
        query,
        update,
        return_document,
    ):
        self.user.update(update["$set"])
        return self.user

    async def update_one(self, query, update):
        self.user.update(update["$set"])
        return SimpleNamespace(matched_count=1)

    async def count_documents(self, query):
        return 1


@pytest.mark.asyncio
async def test_create_user_normalizes_email(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(user_repository, "collection", collection)

    user = await user_repository.create_user(
        email="User@Company.COM ",
        full_name="Company User",
        hashed_password="hashed",
        role=UserRole.EMPLOYEE,
    )

    assert user["email"] == "user@company.com"
    assert user["role"] == UserRole.EMPLOYEE


@pytest.mark.asyncio
async def test_duplicate_email_is_controlled(monkeypatch):
    collection = FakeCollection()
    collection.insert_error = DuplicateKeyError("duplicate")
    monkeypatch.setattr(user_repository, "collection", collection)

    with pytest.raises(user_repository.DuplicateUserEmailError):
        await user_repository.create_user(
            email="user@company.com",
            full_name="Company User",
            hashed_password="hashed",
            role=UserRole.EMPLOYEE,
        )


@pytest.mark.asyncio
async def test_fetch_user_by_email_and_id(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(user_repository, "collection", collection)

    by_email = await user_repository.get_by_email(
        "USER@COMPANY.COM"
    )
    by_id = await user_repository.get_by_id(
        "64b7f11a8b1234567890abcd"
    )

    assert by_email["id"] == by_id["id"]


@pytest.mark.asyncio
async def test_list_and_update_user(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(user_repository, "collection", collection)

    users = await user_repository.list_users(page=1, limit=10)
    updated = await user_repository.update_user(
        users[0]["id"],
        {"role": UserRole.EDITOR},
    )

    assert len(users) == 1
    assert updated["role"] == UserRole.EDITOR


@pytest.mark.asyncio
async def test_deactivate_user(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(user_repository, "collection", collection)

    assert await user_repository.deactivate_user(
        "64b7f11a8b1234567890abcd"
    )
    assert collection.user["is_active"] is False


@pytest.mark.asyncio
async def test_unique_index_initialization(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(user_repository, "collection", collection)

    result = await user_repository.ensure_indexes()

    assert result == ["users_email_unique_idx"]
    assert collection.created_index[1]["unique"] is True
