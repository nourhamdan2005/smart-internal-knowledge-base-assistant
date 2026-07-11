import pytest

from app.repositories import search_repository
from app.repositories.search_repository import (
    calculate_relevance_score,
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


def test_extract_keywords_returns_empty_list_for_only_stop_words():
    result = extract_keywords(
        "What is it and how do I do it?"
    )

    assert result == []


def test_remote_policy_document_has_positive_score():
    document = {
        "title": "Remote Work Policy",
        "content": (
            "Employees may work remotely "
            "with manager approval."
        ),
        "tags": [
            "remote",
            "policy",
        ],
    }

    score = calculate_relevance_score(
        document=document,
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


def test_relevant_document_scores_higher_than_unrelated_document():
    relevant_document = {
        "title": "Remote Work Policy",
        "content": (
            "Employees may work remotely "
            "with manager approval."
        ),
        "tags": [
            "remote",
            "policy",
        ],
    }

    unrelated_document = {
        "title": "Password Reset Guide",
        "content": (
            "Employees should contact IT "
            "to reset their passwords."
        ),
        "tags": [
            "password",
            "IT",
        ],
    }

    relevant_score = calculate_relevance_score(
        document=relevant_document,
        keywords=[
            "remote",
            "work",
            "policy",
        ],
        original_question=(
            "What is the remote work policy?"
        ),
    )

    unrelated_score = calculate_relevance_score(
        document=unrelated_document,
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
async def test_search_documents_ranks_candidates(
    monkeypatch,
):
    candidates = [
        {
            "id": "2",
            "title": "Password Reset Guide",
            "category": "IT",
            "content": (
                "Employees should contact IT "
                "to reset their passwords."
            ),
            "tags": [
                "password",
            ],
        },
        {
            "id": "1",
            "title": "Remote Work Policy",
            "category": "HR",
            "content": (
                "Employees may work remotely "
                "with manager approval."
            ),
            "tags": [
                "remote",
                "policy",
            ],
        },
    ]

    async def fake_search_document_candidates(
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
        "search_document_candidates",
        fake_search_document_candidates,
    )

    result = await search_repository.search_documents(
        question="What is the remote work policy?",
        category="HR",
        limit=1,
    )

    assert len(result) == 1
    assert result[0]["id"] == "1"
    assert result[0]["title"] == (
        "Remote Work Policy"
    )


@pytest.mark.asyncio
async def test_search_documents_returns_empty_for_blank_question(
    monkeypatch,
):
    async def fake_search_document_candidates(
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
        "search_document_candidates",
        fake_search_document_candidates,
    )

    result = await search_repository.search_documents(
        question="   ",
        category="HR",
    )

    assert result == []


@pytest.mark.asyncio
async def test_search_documents_returns_empty_when_no_candidates(
    monkeypatch,
):
    async def fake_search_document_candidates(
        keywords,
        category=None,
        limit=50,
    ):
        return []

    monkeypatch.setattr(
        search_repository,
        "search_document_candidates",
        fake_search_document_candidates,
    )

    result = await search_repository.search_documents(
        question="What is the remote work policy?",
        category="HR",
    )

    assert result == []