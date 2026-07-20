from pydantic import BaseModel, Field


class EmbeddingBackfillFailure(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    chunk_index: int
    error: str


class EmbeddingBackfillResponse(BaseModel):
    total_chunks: int
    processed_chunks: int
    skipped_chunks: int
    failed_chunks: int
    failures: list[EmbeddingBackfillFailure] = Field(
        default_factory=list,
    )