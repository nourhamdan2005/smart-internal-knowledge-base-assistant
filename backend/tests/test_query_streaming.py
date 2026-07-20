import json

import pytest

from app.ai import openai_client
from app.api.v1.endpoints import query
from app.schemas.query import QueryRequest


class ConnectedRequest:
    async def is_disconnected(self):
        return False


async def response_text(response) -> str:
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk.decode() if isinstance(chunk, bytes) else chunk)
    return "".join(chunks)


def events(text: str):
    parsed = []
    for block in text.strip().split("\n\n"):
        lines = block.splitlines()
        parsed.append((lines[0].removeprefix("event: "), json.loads(lines[1].removeprefix("data: "))))
    return parsed


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("What is the policy?", 96),
        ("Summarize the policy", 192),
        ("Give a detailed explanation", 320),
    ],
)
def test_answer_budget_is_intent_aware(monkeypatch, question, expected):
    monkeypatch.setattr(openai_client.settings, "ollama_generation_num_predict", 192)
    assert openai_client.answer_token_budget(question) == expected


@pytest.mark.asyncio
async def test_stream_events_are_ordered_and_utf8_safe(monkeypatch):
    async def fake_prepare(question, category=None):
        return {
            "chunks": [{}],
            "context": "context",
            "sources": [{"chunk_id": "c1", "title": "Policy", "excerpt": "Safe"}],
            "fallback_response": None,
        }

    async def fake_stream(question, context):
        yield "Café "
        yield "policy."

    monkeypatch.setattr(query, "prepare_query", fake_prepare)
    monkeypatch.setattr(query, "stream_answer", fake_stream)
    response = await query.stream_knowledge_base(
        QueryRequest(question="Question"), ConnectedRequest()
    )
    parsed = events(await response_text(response))

    assert [event for event, _ in parsed] == ["status", "status", "delta", "delta", "sources", "done"]
    assert "Café" in "".join(data.get("text", "") for _, data in parsed)


@pytest.mark.asyncio
async def test_stream_reports_generation_failure(monkeypatch):
    async def fake_prepare(question, category=None):
        return {"chunks": [{}], "context": "context", "sources": [], "fallback_response": None}

    async def fake_stream(question, context):
        raise openai_client.AIServiceError("private detail")
        yield ""

    monkeypatch.setattr(query, "prepare_query", fake_prepare)
    monkeypatch.setattr(query, "stream_answer", fake_stream)
    response = await query.stream_knowledge_base(
        QueryRequest(question="Question"), ConnectedRequest()
    )
    parsed = events(await response_text(response))

    assert parsed[-1] == ("error", {"message": "The answer stream was interrupted. Please retry."})


@pytest.mark.asyncio
async def test_empty_retrieval_preserves_fallback(monkeypatch):
    async def fake_prepare(question, category=None):
        return {
            "chunks": [],
            "context": "",
            "sources": [],
            "fallback_response": {"answer": "No grounded evidence."},
        }

    monkeypatch.setattr(query, "prepare_query", fake_prepare)
    response = await query.stream_knowledge_base(
        QueryRequest(question="Question"), ConnectedRequest()
    )
    parsed = events(await response_text(response))

    assert ("delta", {"text": "No grounded evidence."}) in parsed
    assert parsed[-1][0] == "done"
