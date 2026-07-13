from fastapi import APIRouter

from app.schemas.chunk_backfill import (
    ChunkBackfillResponse,
)
from app.services.document_backfill_service import (
    backfill_missing_document_chunks,
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