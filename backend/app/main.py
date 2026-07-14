from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.database_indexes import (
    create_database_indexes,
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    """
    Initialize database infrastructure before serving requests.
    """
    await create_database_indexes()

    yield


app = FastAPI(
    title="Smart Internal Knowledge Base Assistant API",
    description=(
        "Backend API for an AI-powered internal "
        "company knowledge assistant."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)