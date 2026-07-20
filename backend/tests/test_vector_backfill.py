import pytest

from app.services import vector_sync_service
from app.vectorstores.base import (
    VectorOperationStats,
    VectorStoreConfigurationError,
    VectorStoreUnavailableError,
)


def make_chunk(chunk_id, embedding=None, dimensions=None):
    return {
        "id": chunk_id,
        "document_id": "document-1",
        "chunk_index": 0,
        "content": "Employees must use MFA.",
        "document_title": "Security Policy",
        "category": "Security",
        "embedding": embedding,
        "embedding_model": "nomic-embed-text",
        "embedding_dimensions": dimensions,
        "is_active": True,
    }


class RecordingStore:
    collection_name = "document_chunks"

    def __init__(self):
        self.chunk_ids = set()
        self.calls = 0

    async def upsert_chunks(self, points):
        self.calls += 1
        self.chunk_ids.update(point.chunk_id for point in points)
        return VectorOperationStats(
            processed=len(points),
            batches=1,
        )


@pytest.mark.asyncio
async def test_backfill_processes_valid_and_skips_invalid_chunks(
    monkeypatch,
):
    chunks = [
        make_chunk("valid", [1.0, 0.0], 2),
        make_chunk("missing"),
        make_chunk("wrong", [1.0], 1),
    ]
    store = RecordingStore()

    async def fake_get_chunks():
        return chunks

    monkeypatch.setattr(
        vector_sync_service.settings,
        "qdrant_enabled",
        True,
    )
    monkeypatch.setattr(
        vector_sync_service.settings,
        "qdrant_vector_size",
        2,
    )
    monkeypatch.setattr(
        vector_sync_service,
        "get_all_active_chunks",
        fake_get_chunks,
    )
    monkeypatch.setattr(
        vector_sync_service,
        "get_vector_store",
        lambda: store,
    )

    result = await vector_sync_service.backfill_vectors()

    assert result["total_chunks"] == 3
    assert result["eligible_chunks"] == 1
    assert result["processed"] == 1
    assert result["skipped"] == 2
    assert result["failed"] == 0


@pytest.mark.asyncio
async def test_backfill_is_idempotent(monkeypatch):
    chunks = [make_chunk("chunk-1", [1.0, 0.0], 2)]
    store = RecordingStore()

    async def fake_get_chunks():
        return chunks

    monkeypatch.setattr(
        vector_sync_service.settings,
        "qdrant_enabled",
        True,
    )
    monkeypatch.setattr(
        vector_sync_service.settings,
        "qdrant_vector_size",
        2,
    )
    monkeypatch.setattr(
        vector_sync_service,
        "get_all_active_chunks",
        fake_get_chunks,
    )
    monkeypatch.setattr(
        vector_sync_service,
        "get_vector_store",
        lambda: store,
    )

    first = await vector_sync_service.backfill_vectors()
    second = await vector_sync_service.backfill_vectors()

    assert first["processed"] == second["processed"] == 1
    assert store.chunk_ids == {"chunk-1"}


@pytest.mark.asyncio
async def test_backfill_rejects_disabled_qdrant(monkeypatch):
    monkeypatch.setattr(
        vector_sync_service.settings,
        "qdrant_enabled",
        False,
    )

    with pytest.raises(VectorStoreConfigurationError):
        await vector_sync_service.backfill_vectors()


@pytest.mark.asyncio
async def test_backfill_reports_unavailable_qdrant(monkeypatch):
    class UnavailableStore:
        async def upsert_chunks(self, points):
            raise VectorStoreUnavailableError("offline")

    async def fake_get_chunks():
        return [make_chunk("chunk-1", [1.0, 0.0], 2)]

    monkeypatch.setattr(
        vector_sync_service.settings,
        "qdrant_enabled",
        True,
    )
    monkeypatch.setattr(
        vector_sync_service.settings,
        "qdrant_vector_size",
        2,
    )
    monkeypatch.setattr(
        vector_sync_service,
        "get_all_active_chunks",
        fake_get_chunks,
    )
    monkeypatch.setattr(
        vector_sync_service,
        "get_vector_store",
        lambda: UnavailableStore(),
    )

    with pytest.raises(VectorStoreUnavailableError):
        await vector_sync_service.backfill_vectors()
