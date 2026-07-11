import httpx
import pytest
from fastapi import HTTPException

from app.ai import openai_client
from app.api.v1.endpoints import query as query_endpoint
from app.schemas.query import QueryRequest


@pytest.mark.asyncio
async def test_generate_answer_returns_content(monkeypatch):
    async def fake_chat(*args, **kwargs):
        return {
            "message": {
                "content": (
                    "Employees may work remotely "
                    "with manager approval."
                )
            }
        }

    monkeypatch.setattr(
        openai_client.client,
        "chat",
        fake_chat,
    )

    result = await openai_client.generate_answer(
        question="What is the remote work policy?",
        context=(
            "Employees may work remotely "
            "with manager approval."
        ),
    )

    assert result == (
        "Employees may work remotely "
        "with manager approval."
    )


@pytest.mark.asyncio
async def test_generate_answer_rejects_empty_response(monkeypatch):
    async def fake_chat(*args, **kwargs):
        return {
            "message": {
                "content": ""
            }
        }

    monkeypatch.setattr(
        openai_client.client,
        "chat",
        fake_chat,
    )

    with pytest.raises(
        openai_client.AIServiceError,
        match="empty response",
    ):
        await openai_client.generate_answer(
            question="What is the policy?",
            context="Policy information",
        )


@pytest.mark.asyncio
async def test_generate_answer_handles_timeout(monkeypatch):
    async def fake_chat(*args, **kwargs):
        raise httpx.ReadTimeout(
            "Request timed out",
        )

    monkeypatch.setattr(
        openai_client.client,
        "chat",
        fake_chat,
    )

    with pytest.raises(
        openai_client.AIServiceError,
        match="too long",
    ):
        await openai_client.generate_answer(
            question="What is the policy?",
            context="Policy information",
        )


@pytest.mark.asyncio
async def test_generate_answer_handles_connection_error(
    monkeypatch,
):
    request = httpx.Request(
        "POST",
        "http://127.0.0.1:11434/api/chat",
    )

    async def fake_chat(*args, **kwargs):
        raise httpx.ConnectError(
            "Connection refused",
            request=request,
        )

    monkeypatch.setattr(
        openai_client.client,
        "chat",
        fake_chat,
    )

    with pytest.raises(
        openai_client.AIServiceError,
        match="currently unavailable",
    ):
        await openai_client.generate_answer(
            question="What is the policy?",
            context="Policy information",
        )


@pytest.mark.asyncio
async def test_query_endpoint_returns_503_for_ai_service_error(
    monkeypatch,
):
    async def fake_query_documents(*args, **kwargs):
        raise openai_client.AIServiceError(
            "The AI service is currently unavailable."
        )

    monkeypatch.setattr(
        query_endpoint,
        "query_documents",
        fake_query_documents,
    )

    with pytest.raises(HTTPException) as exc_info:
        await query_endpoint.query_knowledge_base(
            QueryRequest(
                question="What is the policy?",
                category="HR",
            )
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == (
        "The AI service is currently unavailable."
    )
