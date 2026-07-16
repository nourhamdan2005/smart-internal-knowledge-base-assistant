from fastapi import APIRouter, HTTPException, status

from app.ai.openai_client import AIServiceError
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import query_documents
from app.vectorstores.base import VectorStoreError

router = APIRouter()


@router.post(
    "/",
    response_model=QueryResponse,
)
async def query_knowledge_base(
    request: QueryRequest,
) -> QueryResponse:
    try:
        result = await query_documents(
            question=request.question,
            category=request.category,
        )

        return QueryResponse(**result)

    except AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except VectorStoreError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Semantic search is temporarily unavailable.",
        ) from exc
