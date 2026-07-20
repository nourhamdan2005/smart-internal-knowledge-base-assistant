import pytest
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from app.api.v1.endpoints import health, maintenance, query
from app.schemas.query import QueryRequest
from app.vectorstores.base import VectorStoreUnavailableError


@pytest.mark.asyncio
async def test_vector_backfill_endpoint_returns_statistics(monkeypatch):
    async def fake_backfill():
        return {
            "total_chunks": 2,
            "eligible_chunks": 1,
            "processed": 1,
            "skipped": 1,
            "failed": 0,
            "batches": 1,
            "collection": "document_chunks",
            "errors": [],
        }

    monkeypatch.setattr(maintenance, "backfill_vectors", fake_backfill)

    result = await maintenance.backfill_chunk_vectors()

    assert result.processed == 1
    assert result.skipped == 1


@pytest.mark.asyncio
async def test_vector_backfill_endpoint_maps_unavailability(monkeypatch):
    async def fake_backfill():
        raise VectorStoreUnavailableError("secret provider details")

    monkeypatch.setattr(maintenance, "backfill_vectors", fake_backfill)

    with pytest.raises(HTTPException) as exc_info:
        await maintenance.backfill_chunk_vectors()

    assert exc_info.value.status_code == 503
    assert "secret" not in exc_info.value.detail


@pytest.mark.asyncio
async def test_query_endpoint_maps_mandatory_vector_failure(monkeypatch):
    async def fake_query_documents(**kwargs):
        raise VectorStoreUnavailableError("secret provider details")

    monkeypatch.setattr(query, "query_documents", fake_query_documents)

    with pytest.raises(HTTPException) as exc_info:
        await query.query_knowledge_base(
            QueryRequest(question="What is the policy?")
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == (
        "Semantic search is temporarily unavailable."
    )


@pytest.mark.asyncio
async def test_readiness_reports_disabled_qdrant(monkeypatch):
    async def database_ready():
        return True

    monkeypatch.setattr(health, "check_database_connection", database_ready)
    monkeypatch.setattr(health.settings, "qdrant_enabled", False)

    result = await health.readiness_check()

    assert result["qdrant"] == "disabled"
    assert result["status"] == "ok"


@pytest.mark.asyncio
async def test_readiness_is_degraded_with_fallback(monkeypatch):
    class Store:
        async def health_check(self):
            return False

    async def database_ready():
        return True

    monkeypatch.setattr(health, "check_database_connection", database_ready)
    monkeypatch.setattr(health.settings, "qdrant_enabled", True)
    monkeypatch.setattr(
        health.settings,
        "qdrant_fallback_enabled",
        True,
    )
    monkeypatch.setattr(health, "get_vector_store", lambda: Store())

    result = await health.readiness_check()

    assert result["status"] == "degraded"
    assert result["qdrant"] == "unavailable"


@pytest.mark.asyncio
async def test_readiness_fails_when_qdrant_is_mandatory(monkeypatch):
    class Store:
        async def health_check(self):
            return False

    async def database_ready():
        return True

    monkeypatch.setattr(health, "check_database_connection", database_ready)
    monkeypatch.setattr(health.settings, "qdrant_enabled", True)
    monkeypatch.setattr(
        health.settings,
        "qdrant_fallback_enabled",
        False,
    )
    monkeypatch.setattr(health, "get_vector_store", lambda: Store())

    result = await health.readiness_check()

    assert isinstance(result, JSONResponse)
    assert result.status_code == 503
