from pydantic import BaseModel, Field


class ChunkBackfillFailure(BaseModel):
    document_id: str
    title: str
    error: str


class ChunkBackfillResponse(BaseModel):
    total_documents: int
    processed_documents: int
    skipped_documents: int
    failed_documents: int
    created_chunks: int
    failures: list[ChunkBackfillFailure] = Field(
        default_factory=list,
    )