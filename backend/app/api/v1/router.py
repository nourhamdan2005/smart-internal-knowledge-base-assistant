from fastapi import APIRouter

from app.api.v1.endpoints import documents, health, query, uploads

api_router = APIRouter()

api_router.include_router(
    health.router,
    tags=["Health"],
)

api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["Documents"],
)

api_router.include_router(
    query.router,
    prefix="/query",
    tags=["Query"],
)

api_router.include_router(
    uploads.router,
    prefix="/uploads",
    tags=["Uploads"],
)