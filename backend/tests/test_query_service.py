import pytest

from app.services import query_service


@pytest.mark.asyncio
async def test_query_documents_uses_chunks_as_context(
    monkeypatch,
):
    monkeypatch.setattr(
        query_service.settings,
        "retrieval_top_k",
        8,
    )

    chunks = [
        {
            "id": "chunk-1",
            "document_id": "document-1",
            "chunk_index": 2,
            "document_title": "Remote Work Policy",
            "category": "HR",
            "content": (
                "Employees may work remotely "
                "with manager approval."
            ),
        },
        {
            "id": "chunk-2",
            "document_id": "document-1",
            "chunk_index": 3,
            "document_title": "Remote Work Policy",
            "category": "HR",
            "content": (
                "Remote employees must remain "
                "available during working hours."
            ),
        },
    ]

    async def fake_hybrid_search_chunks(
        question,
        category=None,
        limit=5,
    ):
        assert question == (
            "What is the remote work policy?"
        )
        assert category == "HR"
        assert limit == 8

        return chunks

    async def fake_generate_answer(
        question,
        context,
    ):
        assert question == (
            "What is the remote work policy?"
        )
        assert "Remote Work Policy" in context
        assert "Chunk: 2" in context
        assert "Chunk: 3" in context
        assert chunks[0]["content"] in context
        assert chunks[1]["content"] in context

        return "Employees may work remotely with approval."

    monkeypatch.setattr(
        query_service,
        "hybrid_search_chunks",
        fake_hybrid_search_chunks,
    )

    monkeypatch.setattr(
        query_service,
        "generate_answer",
        fake_generate_answer,
    )

    result = await query_service.query_documents(
        question="What is the remote work policy?",
        category="HR",
    )

    assert result["answer"] == (
        "Employees may work remotely with approval."
    )

    assert result["sources"] == [
        {
            "chunk_id": "chunk-1",
            "chunk_index": 2,
            "document_id": "document-1",
            "title": "Remote Work Policy",
            "category": "HR",
            "excerpt": (
                "Employees may work remotely "
                "with manager approval."
            ),
        },
        {
            "chunk_id": "chunk-2",
            "chunk_index": 3,
            "document_id": "document-1",
            "title": "Remote Work Policy",
            "category": "HR",
            "excerpt": (
                "Remote employees must remain "
                "available during working hours."
            ),
        },
    ]


@pytest.mark.asyncio
async def test_query_documents_returns_fallback_when_no_chunks(
    monkeypatch,
):
    async def fake_hybrid_search_chunks(
        question,
        category=None,
        limit=5,
    ):
        return []

    async def fake_generate_answer(
        question,
        context,
    ):
        raise AssertionError(
            "AI generation should not run "
            "when no chunks are found."
        )

    monkeypatch.setattr(
        query_service,
        "hybrid_search_chunks",
        fake_hybrid_search_chunks,
    )

    monkeypatch.setattr(
        query_service,
        "generate_answer",
        fake_generate_answer,
    )

    result = await query_service.query_documents(
        question="Unknown information",
        category=None,
    )

    assert result == {
        "question": "Unknown information",
        "answer": (
            "I couldn't find this information "
            "in the available documents."
        ),
        "sources": [],
    }


def test_create_source_excerpt_returns_short_content():
    content = "Employees must use MFA."

    result = query_service.create_source_excerpt(content)

    assert result == content


def test_create_source_excerpt_normalizes_whitespace():
    content = (
        "Employees   must\nuse\tmulti-factor "
        "authentication."
    )

    result = query_service.create_source_excerpt(content)

    assert result == (
        "Employees must use multi-factor "
        "authentication."
    )


def test_create_source_excerpt_shortens_long_content():
    content = (
        "Employees must use multi-factor "
        "authentication for every company "
        "account and must never share their "
        "authentication codes with another "
        "employee or external person."
    )

    result = query_service.create_source_excerpt(
        content,
        max_length=80,
    )

    assert len(result) <= 83
    assert result.endswith("...")
    assert not result.endswith(" ...")
