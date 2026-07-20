import asyncio
import json
import logging

import pytest
from fastapi import Response

from app.api.v1.endpoints import query as query_endpoint
from app.core import query_profiling
from app.schemas.query import QueryRequest


@pytest.mark.asyncio
async def test_stage_timer_records_async_elapsed_time():
    profiler = query_profiling.QueryProfiler(enabled=True)

    async with profiler.stage("embedding_ms"):
        await asyncio.sleep(0.01)

    assert profiler.timing.embedding_ms is not None
    assert 5 <= profiler.timing.embedding_ms < 100


def test_disabled_profiler_does_not_publish_active_profile():
    profiler = query_profiling.QueryProfiler(enabled=False)
    token = query_profiling.activate_query_profiler(profiler)
    try:
        assert query_profiling.get_query_profiler() is None
    finally:
        query_profiling.deactivate_query_profiler(token)


@pytest.mark.asyncio
async def test_endpoint_logs_safe_profile_and_keeps_response_schema(
    monkeypatch, caplog
):
    async def fake_query_documents(question, category=None):
        profiler = query_profiling.get_query_profiler()
        assert profiler is not None
        profiler.set(fallback_path="qdrant_hybrid", final_context_chunks=1)
        return {"question": question, "answer": "Safe answer", "sources": []}

    secret_question = "SECRET QUESTION TEXT"
    monkeypatch.setattr(query_endpoint, "query_documents", fake_query_documents)
    monkeypatch.setattr(query_endpoint.settings, "query_profiling_enabled", True)
    monkeypatch.setattr(query_endpoint.settings, "query_profiling_log_level", "INFO")
    monkeypatch.setattr(
        query_endpoint.settings, "query_profiling_slow_threshold_ms", 999999
    )

    with caplog.at_level(logging.INFO, logger=query_profiling.__name__):
        result = await query_endpoint.query_knowledge_base(
            QueryRequest(question=secret_question), Response()
        )

    assert result.model_dump() == {
        "answer": "Safe answer",
        "sources": [],
    }
    message = next(record.message for record in caplog.records if "query_performance" in record.message)
    assert secret_question not in message
    assert json.loads(message)["fallback_path"] == "qdrant_hybrid"


@pytest.mark.asyncio
async def test_server_timing_header_only_when_enabled(monkeypatch):
    async def fake_query_documents(question, category=None):
        return {"question": question, "answer": "Answer", "sources": []}

    monkeypatch.setattr(query_endpoint, "query_documents", fake_query_documents)
    monkeypatch.setattr(query_endpoint.settings, "query_profiling_enabled", True)
    monkeypatch.setattr(
        query_endpoint.settings, "query_profiling_server_timing_enabled", True
    )
    response = Response()

    await query_endpoint.query_knowledge_base(
        QueryRequest(question="Question"), response
    )

    assert "total;dur=" in response.headers["Server-Timing"]


def test_slow_profile_uses_one_warning_log(monkeypatch, caplog):
    profiler = query_profiling.QueryProfiler(enabled=True)
    profiler.timing.total_ms = 50
    monkeypatch.setattr(
        query_profiling.settings, "query_profiling_slow_threshold_ms", 10
    )

    with caplog.at_level(logging.WARNING, logger=query_profiling.__name__):
        profiler.log()

    records = [record for record in caplog.records if "query_performance" in record.message]
    assert len(records) == 1
    assert json.loads(records[0].message)["slow"] is True
