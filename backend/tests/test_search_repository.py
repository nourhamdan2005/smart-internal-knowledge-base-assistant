import pytest

from app.repositories import search_repository
from app.repositories.search_repository import (
    calculate_chunk_relevance_score,
    extract_keywords,
)


def test_extract_keywords_removes_stop_words():
    result = extract_keywords(
        "What is the remote work policy?"
    )

    assert result == [
        "remote",
        "work",
        "policy",
    ]


def test_extract_keywords_removes_duplicates():
    result = extract_keywords(
        "Remote work and remote policy"
    )

    assert result == [
        "remote",
        "work",
        "policy",
    ]


def test_extract_keywords_returns_empty_for_only_stop_words():
    result = extract_keywords(
        "What is it and how do I do it?"
    )

    assert result == []


def test_relevant_chunk_has_positive_score():
    chunk = {
        "document_title": "Remote Work Policy",
        "content": (
            "Employees may work remotely "
            "with manager approval."
        ),
    }

    score = calculate_chunk_relevance_score(
        chunk=chunk,
        keywords=[
            "remote",
            "work",
            "policy",
        ],
        original_question=(
            "What is the remote work policy?"
        ),
    )

    assert score > 0


def test_relevant_chunk_scores_higher_than_unrelated_chunk():
    relevant_chunk = {
        "document_title": "Remote Work Policy",
        "content": (
            "Employees may work remotely "
            "with manager approval."
        ),
    }

    unrelated_chunk = {
        "document_title": "Password Reset Guide",
        "content": (
            "Employees should contact IT "
            "to reset their passwords."
        ),
    }

    relevant_score = calculate_chunk_relevance_score(
        chunk=relevant_chunk,
        keywords=[
            "remote",
            "work",
            "policy",
        ],
        original_question=(
            "What is the remote work policy?"
        ),
    )

    unrelated_score = calculate_chunk_relevance_score(
        chunk=unrelated_chunk,
        keywords=[
            "remote",
            "work",
            "policy",
        ],
        original_question=(
            "What is the remote work policy?"
        ),
    )

    assert relevant_score > unrelated_score


@pytest.mark.asyncio
async def test_search_chunks_ranks_candidates(
    monkeypatch,
):
    candidates = [
        {
            "id": "chunk-2",
            "document_id": "document-2",
            "chunk_index": 0,
            "document_title": "Password Reset Guide",
            "category": "IT",
            "content": (
                "Employees should contact IT "
                "to reset their passwords."
            ),
        },
        {
            "id": "chunk-1",
            "document_id": "document-1",
            "chunk_index": 0,
            "document_title": "Remote Work Policy",
            "category": "HR",
            "content": (
                "Employees may work remotely "
                "with manager approval."
            ),
        },
    ]

    async def fake_search_chunk_candidates(
        keywords,
        category=None,
        limit=50,
    ):
        assert keywords == [
            "remote",
            "work",
            "policy",
        ]
        assert category == "HR"
        assert limit == 50

        return candidates

    monkeypatch.setattr(
        search_repository,
        "search_chunk_candidates",
        fake_search_chunk_candidates,
    )

    result = await search_repository.search_chunks(
        question="What is the remote work policy?",
        category="HR",
        limit=1,
    )

    assert len(result) == 1
    assert result[0]["id"] == "chunk-1"
    assert result[0]["document_title"] == (
        "Remote Work Policy"
    )


@pytest.mark.asyncio
async def test_search_chunks_returns_empty_for_blank_question(
    monkeypatch,
):
    async def fake_search_chunk_candidates(
        keywords,
        category=None,
        limit=50,
    ):
        raise AssertionError(
            "Database search should not run "
            "for an empty question."
        )

    monkeypatch.setattr(
        search_repository,
        "search_chunk_candidates",
        fake_search_chunk_candidates,
    )

    result = await search_repository.search_chunks(
        question="   ",
        category="HR",
    )

    assert result == []


@pytest.mark.asyncio
async def test_search_chunks_returns_empty_when_no_candidates(
    monkeypatch,
):
    async def fake_search_chunk_candidates(
        keywords,
        category=None,
        limit=50,
    ):
        return []

    monkeypatch.setattr(
        search_repository,
        "search_chunk_candidates",
        fake_search_chunk_candidates,
    )

    result = await search_repository.search_chunks(
        question="What is the remote work policy?",
        category="HR",
    )

    assert result == []