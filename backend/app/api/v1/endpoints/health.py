from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.database import check_database_connection

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

    return {
        "status": "ok",
        "message": "Backend and database are ready",
    }