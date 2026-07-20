from datetime import datetime

import pytest

from app.schemas.document import DocumentCreate, DocumentUpdate
from app.services import document_service


def make_document(
    document_id: str = "64b7f11a8b1234567890abcd",
    title: str = "Security Policy",
    content: str = "Employees must use multi-factor authentication.",
    is_active: bool = True,
) -> dict:
    now = datetime.utcnow()

    return {
        "id": document_id,
        "title": title,
        "category": "Security",
        "content": content,
        "tags": ["security", "mfa"],
        "author": "Admin",
        "is_active": is_active,
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
async def test_create_document_creates_chunks(
    monkeypatch,
):
    document = make_document()
    created_chunks_for: list[str] = []

    async def mock_create_document(document_data):
        return document

    async def mock_create_chunks(created_document):
        created_chunks_for.append(created_document["id"])
        return [{"id": "chunk-1"}]

    monkeypatch.setattr(
        document_service.document_repository,
        "create_document",
        mock_create_document,
    )
    monkeypatch.setattr(
        document_service,
        "create_chunks_for_document",
        mock_create_chunks,
    )

    document_data = DocumentCreate(
        title="Security Policy",
        category="Security",
        content=(
            "Employees must use multi-factor authentication."
        ),
    )

    result = await document_service.create_document(
        document_data
    )

    assert result == document
    assert created_chunks_for == [document["id"]]


@pytest.mark.asyncio
async def test_create_document_removes_document_when_chunking_fails(
    monkeypatch,
):
    document = make_document()
    removed_documents: list[str] = []

    async def mock_create_document(document_data):
        return document

    async def mock_create_chunks(created_document):
        raise RuntimeError("Chunk creation failed")

    async def mock_hard_delete(document_id):
        removed_documents.append(document_id)
        return True

    monkeypatch.setattr(
        document_service.document_repository,
        "create_document",
        mock_create_document,
    )
    monkeypatch.setattr(
        document_service,
        "create_chunks_for_document",
        mock_create_chunks,
    )
    monkeypatch.setattr(
        document_service.document_repository,
        "hard_delete_document",
        mock_hard_delete,
    )

    document_data = DocumentCreate(
        title="Security Policy",
        category="Security",
        content=(
            "Employees must use multi-factor authentication."
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="Chunk creation failed",
    ):
        await document_service.create_document(document_data)

    assert removed_documents == [document["id"]]


@pytest.mark.asyncio
async def test_update_document_regenerates_chunks(
    monkeypatch,
):
    original_document = make_document()
    updated_document = make_document(
        title="Updated Security Policy",
        content=(
            "Employees must use MFA for every company account."
        ),
    )

    deactivated_documents: list[str] = []
    chunked_documents: list[str] = []

    async def mock_get_document(document_id):
        return original_document

    async def mock_update_document(
        document_id,
        document_data,
    ):
        return updated_document

    async def mock_deactivate(document_id):
        deactivated_documents.append(document_id)
        return 2

    async def mock_create_chunks(document):
        chunked_documents.append(document["title"])
        return [{"id": "new-chunk"}]

    monkeypatch.setattr(
        document_service.document_repository,
        "get_document_by_id",
        mock_get_document,
    )
    monkeypatch.setattr(
        document_service.document_repository,
        "update_document",
        mock_update_document,
    )
    monkeypatch.setattr(
        document_service,
        "deactivate_chunks_by_document_id",
        mock_deactivate,
    )
    monkeypatch.setattr(
        document_service,
        "create_chunks_for_document",
        mock_create_chunks,
    )

    update_data = DocumentUpdate(
        title="Updated Security Policy",
        content=(
            "Employees must use MFA for every company account."
        ),
    )

    result = await document_service.update_document(
        original_document["id"],
        update_data,
    )

    assert result == updated_document
    assert deactivated_documents == [
        original_document["id"]
    ]
    assert chunked_documents == [
        "Updated Security Policy"
    ]


@pytest.mark.asyncio
async def test_update_document_rolls_back_when_chunking_fails(
    monkeypatch,
):
    original_document = make_document()
    updated_document = make_document(
        title="Updated Security Policy",
    )

    restored_documents: list[str] = []
    reactivated_documents: list[str] = []

    async def mock_get_document(document_id):
        return original_document

    async def mock_update_document(
        document_id,
        document_data,
    ):
        return updated_document

    async def mock_deactivate(document_id):
        return 2

    async def mock_create_chunks(document):
        raise RuntimeError("Chunk regeneration failed")

    async def mock_restore(document_id, snapshot):
        restored_documents.append(document_id)
        assert snapshot == original_document
        return True

    async def mock_reactivate(document_id):
        reactivated_documents.append(document_id)
        return 2

    monkeypatch.setattr(
        document_service.document_repository,
        "get_document_by_id",
        mock_get_document,
    )
    monkeypatch.setattr(
        document_service.document_repository,
        "update_document",
        mock_update_document,
    )
    monkeypatch.setattr(
        document_service,
        "deactivate_chunks_by_document_id",
        mock_deactivate,
    )
    monkeypatch.setattr(
        document_service,
        "create_chunks_for_document",
        mock_create_chunks,
    )
    monkeypatch.setattr(
        document_service.document_repository,
        "restore_document_snapshot",
        mock_restore,
    )
    monkeypatch.setattr(
        document_service,
        "reactivate_chunks_by_document_id",
        mock_reactivate,
    )

    update_data = DocumentUpdate(
        title="Updated Security Policy",
    )

    with pytest.raises(
        RuntimeError,
        match="Chunk regeneration failed",
    ):
        await document_service.update_document(
            original_document["id"],
            update_data,
        )

    assert restored_documents == [
        original_document["id"]
    ]
    assert reactivated_documents == [
        original_document["id"]
    ]


@pytest.mark.asyncio
async def test_delete_document_deactivates_chunks(
    monkeypatch,
):
    document = make_document()
    deactivated_documents: list[str] = []

    async def mock_get_document(document_id):
        return document

    async def mock_delete_document(document_id):
        return True

    async def mock_deactivate(document_id):
        deactivated_documents.append(document_id)
        return 3

    monkeypatch.setattr(
        document_service.document_repository,
        "get_document_by_id",
        mock_get_document,
    )
    monkeypatch.setattr(
        document_service.document_repository,
        "delete_document",
        mock_delete_document,
    )
    monkeypatch.setattr(
        document_service,
        "deactivate_chunks_by_document_id",
        mock_deactivate,
    )

    result = await document_service.delete_document(
        document["id"]
    )

    assert result is True
    assert deactivated_documents == [document["id"]]


@pytest.mark.asyncio
async def test_delete_document_rolls_back_when_chunk_deactivation_fails(
    monkeypatch,
):
    document = make_document()
    restored_documents: list[str] = []
    reactivated_documents: list[str] = []

    async def mock_get_document(document_id):
        return document

    async def mock_delete_document(document_id):
        return True

    async def mock_deactivate(document_id):
        raise RuntimeError("Chunk deactivation failed")

    async def mock_restore(document_id, snapshot):
        restored_documents.append(document_id)
        assert snapshot == document
        return True

    async def mock_reactivate(document_id):
        reactivated_documents.append(document_id)
        return 1

    monkeypatch.setattr(
        document_service.document_repository,
        "get_document_by_id",
        mock_get_document,
    )
    monkeypatch.setattr(
        document_service.document_repository,
        "delete_document",
        mock_delete_document,
    )
    monkeypatch.setattr(
        document_service,
        "deactivate_chunks_by_document_id",
        mock_deactivate,
    )
    monkeypatch.setattr(
        document_service.document_repository,
        "restore_document_snapshot",
        mock_restore,
    )
    monkeypatch.setattr(
        document_service,
        "reactivate_chunks_by_document_id",
        mock_reactivate,
    )

    with pytest.raises(
        RuntimeError,
        match="Chunk deactivation failed",
    ):
        await document_service.delete_document(
            document["id"]
        )

    assert restored_documents == [document["id"]]
    assert reactivated_documents == [document["id"]]


@pytest.mark.asyncio
async def test_update_missing_document_returns_none(
    monkeypatch,
):
    async def mock_get_document(document_id):
        return None

    monkeypatch.setattr(
        document_service.document_repository,
        "get_document_by_id",
        mock_get_document,
    )

    result = await document_service.update_document(
        "invalid-id",
        DocumentUpdate(title="Updated title"),
    )

    assert result is None


@pytest.mark.asyncio
async def test_delete_missing_document_returns_false(
    monkeypatch,
):
    async def mock_get_document(document_id):
        return None

    monkeypatch.setattr(
        document_service.document_repository,
        "get_document_by_id",
        mock_get_document,
    )

    result = await document_service.delete_document(
        "invalid-id"
    )

    assert result is False