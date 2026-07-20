from datetime import datetime

import pytest

from app.schemas.document import DocumentCreate, DocumentUpdate
from app.services import document_service, vector_sync_service
from app.vectorstores.base import VectorStoreUnavailableError


def make_document(title="Security Policy"):
    now = datetime.utcnow()
    return {
        "id": "64b7f11a8b1234567890abcd",
        "title": title,
        "category": "Security",
        "content": "Employees must use MFA.",
        "tags": [],
        "author": "Admin",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "original_filename": None,
        "extension": None,
        "mime_type": None,
        "file_size": None,
        "checksum": None,
        "uploaded_at": None,
    }


@pytest.mark.asyncio
async def test_document_create_synchronizes_created_chunks(monkeypatch):
    document = make_document()
    chunks = [{"id": "chunk-1"}]
    synchronized = []

    async def create_document(document_data):
        return document

    async def create_chunks(created_document):
        return chunks

    async def sync_chunks(created_chunks):
        synchronized.extend(created_chunks)

    monkeypatch.setattr(
        document_service.document_repository,
        "create_document",
        create_document,
    )
    monkeypatch.setattr(
        document_service,
        "create_chunks_for_document",
        create_chunks,
    )
    monkeypatch.setattr(
        document_service.vector_sync_service,
        "sync_chunks_on_write",
        sync_chunks,
    )

    await document_service.create_document(
        DocumentCreate(
            title=document["title"],
            category=document["category"],
            content=document["content"],
        )
    )

    assert synchronized == chunks


@pytest.mark.asyncio
async def test_document_update_replaces_document_vectors(monkeypatch):
    original = make_document()
    updated = make_document(title="Updated Policy")
    events = []

    async def get_document(document_id):
        return original

    async def update_document(document_id, document_data):
        return updated

    async def deactivate(document_id):
        return 1

    async def create_chunks(document):
        return [{"id": "new-chunk"}]

    async def remove(document_id):
        events.append(("remove", document_id))

    async def sync(chunks):
        events.append(("sync", chunks[0]["id"]))

    monkeypatch.setattr(
        document_service.document_repository,
        "get_document_by_id",
        get_document,
    )
    monkeypatch.setattr(
        document_service.document_repository,
        "update_document",
        update_document,
    )
    monkeypatch.setattr(
        document_service,
        "deactivate_chunks_by_document_id",
        deactivate,
    )
    monkeypatch.setattr(
        document_service,
        "create_chunks_for_document",
        create_chunks,
    )
    monkeypatch.setattr(
        document_service.vector_sync_service,
        "remove_document_on_write",
        remove,
    )
    monkeypatch.setattr(
        document_service.vector_sync_service,
        "sync_chunks_on_write",
        sync,
    )

    await document_service.update_document(
        original["id"],
        DocumentUpdate(title="Updated Policy"),
    )

    assert events == [
        ("remove", original["id"]),
        ("sync", "new-chunk"),
    ]


@pytest.mark.asyncio
async def test_document_delete_removes_document_vectors(monkeypatch):
    document = make_document()
    removed = []

    async def get_document(document_id):
        return document

    async def delete_document(document_id):
        return True

    async def deactivate(document_id):
        return 1

    async def remove(document_id):
        removed.append(document_id)

    monkeypatch.setattr(
        document_service.document_repository,
        "get_document_by_id",
        get_document,
    )
    monkeypatch.setattr(
        document_service.document_repository,
        "delete_document",
        delete_document,
    )
    monkeypatch.setattr(
        document_service,
        "deactivate_chunks_by_document_id",
        deactivate,
    )
    monkeypatch.setattr(
        document_service.vector_sync_service,
        "remove_document_on_write",
        remove,
    )

    assert await document_service.delete_document(document["id"])
    assert removed == [document["id"]]


@pytest.mark.asyncio
async def test_sync_failure_degrades_when_fallback_enabled(monkeypatch):
    chunk = {
        "id": "chunk-1",
        "document_id": "document-1",
        "chunk_index": 0,
        "content": "Policy",
        "document_title": "Policy",
        "category": "HR",
        "embedding": [1.0, 0.0],
        "embedding_model": "model",
        "embedding_dimensions": 2,
        "is_active": True,
    }

    async def fail(chunks):
        raise VectorStoreUnavailableError("offline")

    monkeypatch.setattr(vector_sync_service.settings, "qdrant_enabled", True)
    monkeypatch.setattr(vector_sync_service.settings, "qdrant_sync_on_write", True)
    monkeypatch.setattr(vector_sync_service.settings, "qdrant_fallback_enabled", True)
    monkeypatch.setattr(vector_sync_service.settings, "qdrant_vector_size", 2)
    monkeypatch.setattr(vector_sync_service, "sync_chunks", fail)

    stats = await vector_sync_service.sync_chunks_on_write([chunk])

    assert stats.failed == 1


@pytest.mark.asyncio
async def test_sync_failure_raises_when_qdrant_is_mandatory(monkeypatch):
    async def fail(chunks):
        raise VectorStoreUnavailableError("offline")

    monkeypatch.setattr(vector_sync_service.settings, "qdrant_enabled", True)
    monkeypatch.setattr(vector_sync_service.settings, "qdrant_sync_on_write", True)
    monkeypatch.setattr(vector_sync_service.settings, "qdrant_fallback_enabled", False)
    monkeypatch.setattr(vector_sync_service, "sync_chunks", fail)

    with pytest.raises(VectorStoreUnavailableError):
        await vector_sync_service.sync_chunks_on_write([{}])


@pytest.mark.asyncio
async def test_mandatory_sync_failure_rolls_back_document_create(
    monkeypatch,
):
    document = make_document()
    deactivated = []
    deleted = []

    async def create_document(document_data):
        return document

    async def create_chunks(created_document):
        return [{"id": "new-chunk"}]

    async def fail_sync(chunks):
        raise VectorStoreUnavailableError("offline")

    async def deactivate(chunk_ids):
        deactivated.extend(chunk_ids)
        return len(chunk_ids)

    async def hard_delete(document_id):
        deleted.append(document_id)
        return True

    monkeypatch.setattr(
        document_service.document_repository,
        "create_document",
        create_document,
    )
    monkeypatch.setattr(
        document_service,
        "create_chunks_for_document",
        create_chunks,
    )
    monkeypatch.setattr(
        document_service.vector_sync_service,
        "sync_chunks_on_write",
        fail_sync,
    )
    monkeypatch.setattr(
        document_service,
        "deactivate_chunks_by_ids",
        deactivate,
    )
    monkeypatch.setattr(
        document_service.document_repository,
        "hard_delete_document",
        hard_delete,
    )

    with pytest.raises(VectorStoreUnavailableError):
        await document_service.create_document(
            DocumentCreate(
                title=document["title"],
                category=document["category"],
                content=document["content"],
            )
        )

    assert deactivated == ["new-chunk"]
    assert deleted == [document["id"]]
