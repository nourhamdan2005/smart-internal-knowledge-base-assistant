from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.database_indexes import (
    create_database_indexes,
)
from app.core.config import settings
from app.vectorstores.base import VectorStoreError
from app.vectorstores.factory import (
    close_vector_store,
    get_vector_store,
)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    """
    Initialize database infrastructure before serving requests.
    """
    await create_database_indexes()

    try:
        store = get_vector_store()

        if store is not None:
            try:
                await store.initialize()
            except VectorStoreError:
                if not settings.qdrant_fallback_enabled:
                    raise

                logger.warning(
                    "Qdrant startup initialization failed; the "
                    "application will use retrieval fallback",
                    exc_info=True,
                )

        yield
    finally:
        await close_vector_store()


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
