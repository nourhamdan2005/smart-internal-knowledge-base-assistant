import logging
import math
from typing import Any

from app.core.config import settings
from app.repositories.document_chunk_repository import (
    get_all_active_chunks,
    get_chunks_by_document_id,
)
from app.vectorstores.base import (
    VectorOperationStats,
    VectorPoint,
    VectorStoreConfigurationError,
    VectorStoreError,
    VectorStoreUnavailableError,
    VectorValidationError,
)
from app.vectorstores.factory import get_vector_store


logger = logging.getLogger(__name__)


def chunk_to_vector_point(
    chunk: dict[str, Any],
) -> VectorPoint:
    """Convert an authoritative MongoDB chunk to a vector point."""
    embedding = chunk.get("embedding")

    if (
        not isinstance(embedding, list)
        or not embedding
        or len(embedding) != settings.qdrant_vector_size
        or chunk.get("embedding_dimensions") != len(embedding)
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            for value in embedding
        )
    ):
        raise VectorValidationError(
            "Chunk does not contain a valid configured embedding."
        )

    return VectorPoint(
        chunk_id=str(chunk["id"]),
        document_id=str(chunk["document_id"]),
        embedding=[float(value) for value in embedding],
        content=str(chunk["content"]),
        title=str(chunk["document_title"]),
        category=str(chunk["category"]),
        chunk_index=int(chunk["chunk_index"]),
        is_active=bool(chunk.get("is_active", True)),
        embedding_model=str(chunk.get("embedding_model", "")),
        embedding_dimensions=int(
            chunk.get("embedding_dimensions", 0)
        ),
    )


def _require_vector_store():
    store = get_vector_store()

    if store is None:
        raise VectorStoreConfigurationError(
            "Qdrant integration is disabled."
        )

    return store


async def sync_chunks(
    chunks: list[dict[str, Any]],
) -> VectorOperationStats:
    """Upsert valid MongoDB chunks through the vector abstraction."""
    points = [chunk_to_vector_point(chunk) for chunk in chunks]

    if not points:
        return VectorOperationStats()

    return await _require_vector_store().upsert_chunks(points)


async def sync_chunks_on_write(
    chunks: list[dict[str, Any]],
) -> VectorOperationStats:
    """Synchronize a write using configured resilience policy."""
    if not settings.qdrant_enabled or not settings.qdrant_sync_on_write:
        return VectorOperationStats()

    try:
        return await sync_chunks(chunks)
    except (VectorStoreError, KeyError, TypeError, ValueError):
        if not settings.qdrant_fallback_enabled:
            raise

        logger.warning(
            "Vector synchronization failed; MongoDB remains "
            "authoritative",
            exc_info=True,
        )
        return VectorOperationStats(failed=len(chunks))


async def remove_document(
    document_id: str,
) -> int:
    """Remove one document from the configured vector store."""
    return await _require_vector_store().delete_by_document_id(
        document_id
    )


async def remove_document_on_write(
    document_id: str,
) -> int:
    """Delete vectors using configured resilience policy."""
    if not settings.qdrant_enabled or not settings.qdrant_sync_on_write:
        return 0

    try:
        return await remove_document(document_id)
    except VectorStoreError:
        if not settings.qdrant_fallback_enabled:
            raise

        logger.warning(
            "Vector deletion failed for document %s; stale points "
            "will be rejected by MongoDB hydration",
            document_id,
            exc_info=True,
        )
        return 0


async def sync_document_on_write(
    document_id: str,
) -> VectorOperationStats:
    """Synchronize all currently active chunks for a document."""
    chunks = await get_chunks_by_document_id(document_id)
    return await sync_chunks_on_write(chunks)


async def backfill_vectors() -> dict[str, Any]:
    """Idempotently copy eligible active MongoDB chunks to Qdrant."""
    if not settings.qdrant_enabled:
        raise VectorStoreConfigurationError(
            "Qdrant integration is disabled."
        )

    chunks = await get_all_active_chunks()
    eligible_points: list[VectorPoint] = []
    skipped = 0

    for chunk in chunks:
        try:
            eligible_points.append(chunk_to_vector_point(chunk))
        except (VectorValidationError, KeyError, TypeError, ValueError):
            skipped += 1

    result: dict[str, Any] = {
        "total_chunks": len(chunks),
        "eligible_chunks": len(eligible_points),
        "processed": 0,
        "skipped": skipped,
        "failed": 0,
        "batches": 0,
        "collection": settings.qdrant_collection_name,
        "errors": [],
    }
    store = _require_vector_store()
    unavailable_error: VectorStoreError | None = None

    for start in range(
        0,
        len(eligible_points),
        settings.qdrant_batch_size,
    ):
        batch = eligible_points[
            start : start + settings.qdrant_batch_size
        ]
        result["batches"] += 1

        try:
            stats = await store.upsert_chunks(batch)
            result["processed"] += stats.processed
            result["failed"] += stats.failed
        except VectorStoreError as exc:
            unavailable_error = exc
            result["failed"] += len(batch)
            result["errors"].append(
                "A vector batch could not be synchronized."
            )

    if (
        eligible_points
        and result["processed"] == 0
        and result["failed"] == len(eligible_points)
        and unavailable_error is not None
    ):
        raise VectorStoreUnavailableError(
            "Vector backfill could not reach Qdrant."
        ) from unavailable_error

    return result
