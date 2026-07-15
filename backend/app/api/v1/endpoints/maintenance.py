from fastapi import APIRouter

from app.schemas.chunk_backfill import (
    ChunkBackfillResponse,
)
from app.schemas.embedding_backfill import (
    EmbeddingBackfillResponse,
)
from app.services.document_backfill_service import (
    backfill_missing_document_chunks,
)
from app.services.embedding_backfill_service import (
    backfill_missing_chunk_embeddings,
)


router = APIRouter()


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