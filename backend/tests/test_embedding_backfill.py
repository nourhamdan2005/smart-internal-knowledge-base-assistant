import pytest

from app.services import embedding_backfill_service


def make_chunk(
    chunk_id: str,
    embedding=None,
    embedding_model=None,
    embedding_dimensions=None,
):
    return {
        "id": chunk_id,
        "document_id": "document-1",
        "chunk_index": 0,
        "content": "Employees must use MFA.",
        "document_title": "Security Policy",
        "category": "Security",
        "embedding": embedding,
        "embedding_model": embedding_model,
        "embedding_dimensions": embedding_dimensions,
        "is_active": True,
    }


def test_chunk_has_valid_embedding():
    chunk = make_chunk(
        chunk_id="chunk-1",
        embedding=[0.1, 0.2, 0.3],
        embedding_model="nomic-embed-text",
        embedding_dimensions=3,
    )

    assert (
        embedding_backfill_service
        .chunk_has_valid_embedding(chunk)
    )


def test_chunk_without_embedding_is_invalid():
    chunk = make_chunk(
        chunk_id="chunk-1",
    )

    assert not (
        embedding_backfill_service
        .chunk_has_valid_embedding(chunk)
    )


@pytest.mark.asyncio
async def test_embedding_backfill_processes_missing_embeddings(
    monkeypatch,
):
    chunks = [
        make_chunk("chunk-1"),
        make_chunk(
            "chunk-2",
            embedding=[0.4, 0.5],
            embedding_model="nomic-embed-text",
            embedding_dimensions=2,
        ),
    ]

    updated_chunks: list[str] = []

    async def fake_get_all_active_chunks():
        return chunks

    async def fake_generate_embedding(text):
        assert text == "Employees must use MFA."

        return [0.1, 0.2, 0.3]

    async def fake_update_chunk_embedding(
        chunk_id,
        embedding,
        embedding_model,
    ):
        updated_chunks.append(chunk_id)

        assert embedding == [0.1, 0.2, 0.3]
        assert embedding_model == "nomic-embed-text"

        return True

    monkeypatch.setattr(
        embedding_backfill_service,
        "get_all_active_chunks",
        fake_get_all_active_chunks,
    )

    monkeypatch.setattr(
        embedding_backfill_service,
        "generate_embedding",
        fake_generate_embedding,
    )

    monkeypatch.setattr(
        embedding_backfill_service,
        "update_chunk_embedding",
        fake_update_chunk_embedding,
    )

    result = await (
        embedding_backfill_service
        .backfill_missing_chunk_embeddings()
    )

    assert result == {
        "total_chunks": 2,
        "processed_chunks": 1,
        "skipped_chunks": 1,
        "failed_chunks": 0,
        "failures": [],
    }

    assert updated_chunks == ["chunk-1"]


@pytest.mark.asyncio
async def test_embedding_backfill_reports_failures(
    monkeypatch,
):
    chunk = make_chunk("chunk-1")

    async def fake_get_all_active_chunks():
        return [chunk]

    async def fake_generate_embedding(text):
        raise RuntimeError(
            "Embedding service unavailable"
        )

    monkeypatch.setattr(
        embedding_backfill_service,
        "get_all_active_chunks",
        fake_get_all_active_chunks,
    )

    monkeypatch.setattr(
        embedding_backfill_service,
        "generate_embedding",
        fake_generate_embedding,
    )

    result = await (
        embedding_backfill_service
        .backfill_missing_chunk_embeddings()
    )

    assert result["processed_chunks"] == 0
    assert result["skipped_chunks"] == 0
    assert result["failed_chunks"] == 1

    assert result["failures"] == [
        {
            "chunk_id": "chunk-1",
            "document_id": "document-1",
            "document_title": "Security Policy",
            "chunk_index": 0,
            "error": "Embedding service unavailable",
        }
    ]


@pytest.mark.asyncio
async def test_embedding_backfill_handles_empty_database(
    monkeypatch,
):
    async def fake_get_all_active_chunks():
        return []

    monkeypatch.setattr(
        embedding_backfill_service,
        "get_all_active_chunks",
        fake_get_all_active_chunks,
    )

    result = await (
        embedding_backfill_service
        .backfill_missing_chunk_embeddings()
    )

    assert result == {
        "total_chunks": 0,
        "processed_chunks": 0,
        "skipped_chunks": 0,
        "failed_chunks": 0,
        "failures": [],
    }


@pytest.mark.asyncio
async def test_embedding_backfill_is_idempotent(
    monkeypatch,
):
    chunks = [
        make_chunk(
            "chunk-1",
            embedding=[0.1, 0.2, 0.3],
            embedding_model="nomic-embed-text",
            embedding_dimensions=3,
        ),
        make_chunk(
            "chunk-2",
            embedding=[0.4, 0.5, 0.6],
            embedding_model="nomic-embed-text",
            embedding_dimensions=3,
        ),
    ]

    async def fake_get_all_active_chunks():
        return chunks

    async def fake_generate_embedding(text):
        raise AssertionError(
            "Embedding generation must not run "
            "for valid chunks."
        )

    monkeypatch.setattr(
        embedding_backfill_service,
        "get_all_active_chunks",
        fake_get_all_active_chunks,
    )

    monkeypatch.setattr(
        embedding_backfill_service,
        "generate_embedding",
        fake_generate_embedding,
    )

    result = await (
        embedding_backfill_service
        .backfill_missing_chunk_embeddings()
    )

    assert result == {
        "total_chunks": 2,
        "processed_chunks": 0,
        "skipped_chunks": 2,
        "failed_chunks": 0,
        "failures": [],
    }