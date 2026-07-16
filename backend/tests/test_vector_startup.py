import pytest

from app import main
from app.vectorstores.base import VectorStoreUnavailableError


class FakeStore:
    def __init__(self, fail=False):
        self.fail = fail
        self.initialized = 0

    async def initialize(self):
        self.initialized += 1
        if self.fail:
            raise VectorStoreUnavailableError("offline")


@pytest.mark.asyncio
async def test_lifespan_initializes_and_closes_shared_store(monkeypatch):
    store = FakeStore()
    closed = 0

    async def indexes():
        return {}

    async def close():
        nonlocal closed
        closed += 1

    monkeypatch.setattr(main.settings, "qdrant_enabled", True)
    monkeypatch.setattr(main, "create_database_indexes", indexes)
    monkeypatch.setattr(main, "get_vector_store", lambda: store)
    monkeypatch.setattr(main, "close_vector_store", close)

    async with main.lifespan(main.app):
        assert store.initialized == 1

    assert closed == 1


@pytest.mark.asyncio
async def test_fallback_enabled_startup_survives_qdrant_failure(
    monkeypatch,
):
    store = FakeStore(fail=True)

    async def indexes():
        return {}

    async def close():
        return None

    monkeypatch.setattr(main.settings, "qdrant_enabled", True)
    monkeypatch.setattr(
        main.settings,
        "qdrant_fallback_enabled",
        True,
    )
    monkeypatch.setattr(main, "create_database_indexes", indexes)
    monkeypatch.setattr(main, "get_vector_store", lambda: store)
    monkeypatch.setattr(main, "close_vector_store", close)

    async with main.lifespan(main.app):
        pass

    assert store.initialized == 1


@pytest.mark.asyncio
async def test_mandatory_qdrant_failure_stops_startup(monkeypatch):
    store = FakeStore(fail=True)

    async def indexes():
        return {}

    monkeypatch.setattr(main.settings, "qdrant_enabled", True)
    monkeypatch.setattr(
        main.settings,
        "qdrant_fallback_enabled",
        False,
    )
    monkeypatch.setattr(main, "create_database_indexes", indexes)
    monkeypatch.setattr(main, "get_vector_store", lambda: store)

    with pytest.raises(VectorStoreUnavailableError):
        async with main.lifespan(main.app):
            pass
