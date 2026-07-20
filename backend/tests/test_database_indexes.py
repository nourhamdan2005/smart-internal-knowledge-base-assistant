import pytest

from app.core import database_indexes


class FakeCollection:
    def __init__(self):
        self.created_indexes = None
        self.index_metadata = {
            "_id_": {
                "key": [
                    (
                        "_id",
                        1,
                    )
                ]
            }
        }

    async def create_indexes(
        self,
        indexes,
    ):
        self.created_indexes = indexes

        return [
            index.document["name"]
            for index in indexes
        ]

    async def index_information(self):
        return self.index_metadata


class FakeDatabase:
    def __init__(self):
        self.collections = {
            "documents": FakeCollection(),
            "document_chunks": FakeCollection(),
            "users": FakeCollection(),
        }

    def __getitem__(
        self,
        collection_name,
    ):
        return self.collections[collection_name]


@pytest.mark.asyncio
async def test_create_database_indexes_creates_all_indexes(
    monkeypatch,
):
    fake_database = FakeDatabase()

    monkeypatch.setattr(
        database_indexes,
        "database",
        fake_database,
    )

    result = (
        await database_indexes.create_database_indexes()
    )

    assert result["documents"] == [
        "documents_is_active_idx",
        "documents_category_active_idx",
        "documents_active_created_at_idx",
        "documents_checksum_active_idx",
    ]

    assert result["document_chunks"] == [
        "chunks_document_active_idx",
        "chunks_category_active_idx",
        "chunks_title_active_idx",
        "chunks_document_index_idx",
        "chunks_is_active_idx",
    ]

    assert result["users"] == [
        "users_email_unique_idx",
        "users_role_active_idx",
    ]

    documents_collection = (
        fake_database.collections["documents"]
    )

    chunks_collection = (
        fake_database.collections["document_chunks"]
    )

    assert len(
        documents_collection.created_indexes
    ) == len(
        database_indexes.DOCUMENT_INDEXES
    )

    assert len(
        chunks_collection.created_indexes
    ) == len(
        database_indexes.DOCUMENT_CHUNK_INDEXES
    )


@pytest.mark.asyncio
async def test_get_database_index_information(
    monkeypatch,
):
    fake_database = FakeDatabase()

    monkeypatch.setattr(
        database_indexes,
        "database",
        fake_database,
    )

    result = (
        await database_indexes
        .get_database_index_information()
    )

    assert "_id_" in result["documents"]
    assert "_id_" in result["document_chunks"]
    assert "_id_" in result["users"]


def test_document_indexes_have_unique_names():
    names = [
        index.document["name"]
        for index in database_indexes.DOCUMENT_INDEXES
    ]

    assert len(names) == len(set(names))


def test_chunk_indexes_have_unique_names():
    names = [
        index.document["name"]
        for index in (
            database_indexes.DOCUMENT_CHUNK_INDEXES
        )
    ]

    assert len(names) == len(set(names))


def test_user_indexes_have_unique_names():
    names = [
        index.document["name"]
        for index in database_indexes.USER_INDEXES
    ]

    assert len(names) == len(set(names))
