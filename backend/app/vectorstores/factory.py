from app.core.config import settings
from app.vectorstores.base import VectorStore
from app.vectorstores.qdrant_store import QdrantVectorStore


_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore | None:
    """Return the process-wide vector store when enabled."""
    global _vector_store

    if not settings.qdrant_enabled:
        return None

    if _vector_store is None:
        _vector_store = QdrantVectorStore(settings)

    return _vector_store


def set_vector_store(store: VectorStore | None) -> None:
    """Override the shared store, primarily for tests."""
    global _vector_store
    _vector_store = store


async def close_vector_store() -> None:
    """Close and clear the shared vector store."""
    global _vector_store

    if _vector_store is not None:
        await _vector_store.close()

    _vector_store = None
