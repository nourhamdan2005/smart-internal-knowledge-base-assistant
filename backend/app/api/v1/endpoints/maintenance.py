from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.chunk_backfill import (
    ChunkBackfillResponse,
)
from app.schemas.embedding_backfill import (
    EmbeddingBackfillResponse,
)
from app.schemas.vector_backfill import VectorBackfillResponse
from app.services.document_backfill_service import (
    backfill_missing_document_chunks,
)
from app.services.embedding_backfill_service import (
    backfill_missing_chunk_embeddings,
)
from app.services.vector_sync_service import backfill_vectors
from app.vectorstores.base import VectorStoreError
from app.dependencies.auth import require_admin


router = APIRouter(dependencies=[Depends(require_admin)])


@router.post(
    "/backfill-chunks",
    response_model=ChunkBackfillResponse,
)
async def backfill_document_chunks() -> ChunkBackfillResponse:
    """
    Create chunks for active legacy documents that do not
    already have active chunks.
    """
    result = await backfill_missing_document_chunks()

    return ChunkBackfillResponse(**result)


@router.post(
    "/backfill-embeddings",
    response_model=EmbeddingBackfillResponse,
)
async def backfill_chunk_embeddings() -> (
    EmbeddingBackfillResponse
):
    """
    Generate embeddings for active chunks that do not
    already contain valid embeddings.
    """
    result = await backfill_missing_chunk_embeddings()

    return EmbeddingBackfillResponse(**result)


@router.post(
    "/backfill-vectors",
    response_model=VectorBackfillResponse,
)
async def backfill_chunk_vectors() -> VectorBackfillResponse:
    """Copy eligible active MongoDB chunk vectors to Qdrant."""
    try:
        result = await backfill_vectors()
    except VectorStoreError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Vector storage is disabled or temporarily "
                "unavailable."
            ),
        ) from exc

    return VectorBackfillResponse(**result)
