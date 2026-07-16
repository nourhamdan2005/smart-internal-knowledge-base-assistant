import pytest

from app.core.config import settings
from app.vectorstores.factory import set_vector_store


@pytest.fixture(autouse=True)
def disable_external_vector_store(monkeypatch):
    """Keep unit tests independent from a local Qdrant process."""
    monkeypatch.setattr(settings, "qdrant_enabled", False)
    set_vector_store(None)

    yield

    set_vector_store(None)
