from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    category: str | None = None


class QuerySource(BaseModel):
    chunk_id: str
    chunk_index: int
    document_id: str
    title: str
    category: str
    excerpt: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[QuerySource]