import pytest

from app.services import document_backfill_service
from app.services.document_chunking_service import (
    DocumentChunkingError,
)


@pytest.mark.asyncio
async def test_backfill_creates_only_missing_chunks(
    monkeypatch,
):
    documents = [
        {
            "id": "document-1",
            "title": "Existing Policy",
            "category": "HR",
            "content": "Existing content.",
        },
        {
            "id": "document-2",
            "title": "Legacy Policy",
            "category": "IT",
            "content": "Legacy content.",
        },
    ]

    async def fake_get_all_active_documents():
        return documents

    async def fake_get_chunked_document_ids():
        return {"document-1"}

    async def fake_create_chunks(document):
        assert document["id"] == "document-2"

        return [
            {"id": "chunk-1"},
            {"id": "chunk-2"},
        ]

    monkeypatch.setattr(
        document_backfill_service,
        "get_all_active_documents",
        fake_get_all_active_documents,
    )

    monkeypatch.setattr(
        document_backfill_service,
        "get_document_ids_with_active_chunks",
        fake_get_chunked_document_ids,
    )

    monkeypatch.setattr(
        document_backfill_service,
        "create_chunks_for_document",
        fake_create_chunks,
    )

    result = await (
        document_backfill_service
        .backfill_missing_document_chunks()
    )

    assert result == {
        "total_documents": 2,
        "processed_documents": 1,
        "skipped_documents": 1,
        "failed_documents": 0,
        "created_chunks": 2,
        "failures": [],
    }


@pytest.mark.asyncio
async def test_backfill_reports_invalid_documents(
    monkeypatch,
):
    documents = [
        {
            "id": "document-1",
            "title": "Empty Policy",
            "category": "HR",
            "content": "",
        },
    ]

    async def fake_get_all_active_documents():
        return documents

    async def fake_get_chunked_document_ids():
        return set()

    async def fake_create_chunks(document):
        raise DocumentChunkingError(
            "Document content cannot be empty."
        )

    monkeypatch.setattr(
        document_backfill_service,
        "get_all_active_documents",
        fake_get_all_active_documents,
    )

    monkeypatch.setattr(
        document_backfill_service,
        "get_document_ids_with_active_chunks",
        fake_get_chunked_document_ids,
    )

    monkeypatch.setattr(
        document_backfill_service,
        "create_chunks_for_document",
        fake_create_chunks,
    )

    result = await (
        document_backfill_service
        .backfill_missing_document_chunks()
    )

    assert result["processed_documents"] == 0
    assert result["failed_documents"] == 1
    assert result["created_chunks"] == 0

    assert result["failures"] == [
        {
            "document_id": "document-1",
            "title": "Empty Policy",
            "error": (
                "Document content cannot be empty."
            ),
        }
    ]


@pytest.mark.asyncio
async def test_backfill_handles_empty_database(
    monkeypatch,
):
    async def fake_get_all_active_documents():
        return []

    async def fake_get_chunked_document_ids():
        return set()

    monkeypatch.setattr(
        document_backfill_service,
        "get_all_active_documents",
        fake_get_all_active_documents,
    )

    monkeypatch.setattr(
        document_backfill_service,
        "get_document_ids_with_active_chunks",
        fake_get_chunked_document_ids,
    )

    result = await (
        document_backfill_service
        .backfill_missing_document_chunks()
    )

    assert result == {
        "total_documents": 0,
        "processed_documents": 0,
        "skipped_documents": 0,
        "failed_documents": 0,
        "created_chunks": 0,
        "failures": [],
    }