import logging
from typing import Any

from app.repositories import document_repository
from app.repositories.document_chunk_repository import (
    deactivate_chunks_by_ids,
    deactivate_chunks_by_document_id,
    reactivate_chunks_by_document_id,
)
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.services.document_chunk_service import (
    create_chunks_for_document,
)
from app.services import vector_sync_service


logger = logging.getLogger(__name__)


async def create_document(
    document_data: DocumentCreate,
) -> dict[str, Any]:
    """
    Create a document and its chunks.

    If chunk creation fails, remove the newly created document
    so the database is not left in an incomplete state.
    """
    document = await document_repository.create_document(
        document_data
    )

    created_chunks: list[dict[str, Any]] = []

    try:
        created_chunks = await create_chunks_for_document(document)
        await vector_sync_service.sync_chunks_on_write(
            created_chunks
        )
    except Exception:
        await deactivate_chunks_by_ids(
            [
                str(chunk.get("id", ""))
                for chunk in created_chunks
            ]
        )
        await document_repository.hard_delete_document(
            document["id"]
        )
        raise

    return document


async def get_documents(
    category: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
    sort: str = "-created_at",
) -> list[dict[str, Any]]:
    return await document_repository.get_documents(
        category=category,
        search=search,
        page=page,
        limit=limit,
        sort=sort,
    )


async def get_document_by_id(
    document_id: str,
) -> dict[str, Any] | None:
    return await document_repository.get_document_by_id(
        document_id
    )


async def update_document(
    document_id: str,
    document_data: DocumentUpdate,
) -> dict[str, Any] | None:
    """
    Update a document and regenerate its chunks.

    If fresh chunk creation fails, restore the document and its
    previously active chunks.
    """
    original_document = (
        await document_repository.get_document_by_id(
            document_id
        )
    )

    if original_document is None:
        return None

    updated_document = await document_repository.update_document(
        document_id,
        document_data,
    )

    if updated_document is None:
        return None

    created_chunks: list[dict[str, Any]] = []

    try:
        await deactivate_chunks_by_document_id(document_id)

        if updated_document["is_active"]:
            created_chunks = await create_chunks_for_document(
                updated_document
            )

        await vector_sync_service.remove_document_on_write(
            document_id
        )
        await vector_sync_service.sync_chunks_on_write(
            created_chunks
        )

    except Exception:
        await deactivate_chunks_by_ids(
            [
                str(chunk.get("id", ""))
                for chunk in created_chunks
            ]
        )
        await document_repository.restore_document_snapshot(
            document_id,
            original_document,
        )

        await reactivate_chunks_by_document_id(document_id)

        try:
            await vector_sync_service.remove_document_on_write(
                document_id
            )
            await vector_sync_service.sync_document_on_write(
                document_id
            )
        except Exception:
            logger.exception(
                "Failed to restore vector state for document %s",
                document_id,
            )

        raise

    return updated_document


async def delete_document(
    document_id: str,
) -> bool:
    """
    Soft-delete a document and deactivate all related chunks.

    If chunk deactivation fails, restore the original document.
    """
    original_document = (
        await document_repository.get_document_by_id(
            document_id
        )
    )

    if original_document is None:
        return False

    deleted = await document_repository.delete_document(
        document_id
    )

    if not deleted:
        return False

    try:
        await deactivate_chunks_by_document_id(document_id)
        await vector_sync_service.remove_document_on_write(
            document_id
        )
    except Exception:
        await document_repository.restore_document_snapshot(
            document_id,
            original_document,
        )

        await reactivate_chunks_by_document_id(document_id)

        try:
            await vector_sync_service.sync_document_on_write(
                document_id
            )
        except Exception:
            logger.exception(
                "Failed to restore vector state for document %s",
                document_id,
            )

        raise

    return True
