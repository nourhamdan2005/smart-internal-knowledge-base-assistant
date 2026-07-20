from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.database import check_database_connection
from app.core.config import settings
from app.vectorstores.factory import get_vector_store

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Backend is running successfully",
    }


@router.get("/ready")
async def readiness_check():
    is_db_connected = await check_database_connection()

    if not is_db_connected:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "message": "Database is not reachable",
            },
        )

    if not settings.qdrant_enabled:
        return {
            "status": "ok",
            "message": "Backend and database are ready",
            "qdrant": "disabled",
        }

    store = get_vector_store()
    qdrant_ready = (
        await store.health_check()
        if store is not None
        else False
    )

    if not qdrant_ready and not settings.qdrant_fallback_enabled:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "message": "Vector storage is not reachable",
                "qdrant": "unavailable",
            },
        )

    return {
        "status": "ok" if qdrant_ready else "degraded",
        "message": (
            "Backend, database, and vector storage are ready"
            if qdrant_ready
            else "Backend and database are ready; vector fallback is active"
        ),
        "qdrant": "ready" if qdrant_ready else "unavailable",
    }
