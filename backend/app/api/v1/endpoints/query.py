from fastapi import APIRouter

from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import query_documents

router = APIRouter()


@router.post("/", response_model=QueryResponse)
async def query_knowledge_base(query_data: QueryRequest):
    return await query_documents(
        question=query_data.question,
        category=query_data.category,
    )