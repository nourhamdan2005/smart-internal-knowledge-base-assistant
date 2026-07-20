import pytest

from app.core.config import settings
from app.vectorstores.factory import set_vector_store


@pytest.fixture(autouse=True)
def disable_external_vector_store(monkeypatch):
    """Keep legacy tests independent from external auth/vector services."""
    monkeypatch.setattr(settings, "qdrant_enabled", False)
    monkeypatch.setattr(settings, "auth_enabled", False)
    set_vector_store(None)

    yield

    set_vector_store(None)
