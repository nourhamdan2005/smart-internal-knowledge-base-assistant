from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    documents,
    health,
    maintenance,
    query,
    uploads,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)

api_router.include_router(
    health.router,
    tags=["Health"],
)

api_router.include_router(
    maintenance.router,
    prefix="/maintenance",
    tags=["Maintenance"],
)

# Preserve the original doubled route as a compatibility alias.
api_router.include_router(
    documents.router,
    prefix="/documents/documents",
    tags=["Documents"],
    include_in_schema=False,
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
