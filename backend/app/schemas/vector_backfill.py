from pydantic import BaseModel, Field


class VectorBackfillResponse(BaseModel):
    total_chunks: int
    eligible_chunks: int
    processed: int
    skipped: int
    failed: int
    batches: int
    collection: str
    errors: list[str] = Field(default_factory=list)
