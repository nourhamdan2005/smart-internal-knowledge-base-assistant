from datetime import datetime

from pydantic import BaseModel, Field


class DocumentChunkCreate(BaseModel):
    document_id: str
    chunk_index: int
    content: str
    start_character: int
    end_character: int
    character_count: int
    category: str
    document_title: str

    embedding: list[float] | None = None
    embedding_model: str | None = None
    embedding_dimensions: int | None = None

    is_active: bool = True


class DocumentChunkResponse(DocumentChunkCreate):
    id: str
    created_at: datetime
    updated_at: datetime


class DocumentChunkList(BaseModel):
    chunks: list[DocumentChunkResponse] = Field(
        default_factory=list
    )