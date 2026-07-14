import pytest

from app.repositories import search_repository
from app.repositories.search_repository import (
    calculate_chunk_relevance_score,
    count_word_occurrences,
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

def test_count_word_occurrences_uses_whole_words():
    result = count_word_occurrences(
        "Work workers working work.",
        "work",
    )

    assert result == 2


def test_content_matches_receive_more_weight_than_title_matches():
    title_match_chunk = {
        "document_title": "MFA Security Policy",
        "content": "General company information.",
    }

    content_match_chunk = {
        "document_title": "General Policy",
        "content": "MFA is mandatory for all employees.",
    }

    title_score = calculate_chunk_relevance_score(
        chunk=title_match_chunk,
        keywords=["mfa"],
        original_question="Is MFA mandatory?",
    )

    content_score = calculate_chunk_relevance_score(
        chunk=content_match_chunk,
        keywords=["mfa"],
        original_question="Is MFA mandatory?",
    )

    assert content_score > title_score


def test_repeated_content_matches_increase_score():
    single_match_chunk = {
        "document_title": "Security Policy",
        "content": "MFA is mandatory.",
    }

    repeated_match_chunk = {
        "document_title": "Security Policy",
        "content": (
            "MFA is mandatory. MFA protects accounts. "
            "MFA must remain enabled."
        ),
    }

    single_score = calculate_chunk_relevance_score(
        chunk=single_match_chunk,
        keywords=["mfa"],
        original_question="What is the MFA policy?",
    )

    repeated_score = calculate_chunk_relevance_score(
        chunk=repeated_match_chunk,
        keywords=["mfa"],
        original_question="What is the MFA policy?",
    )

    assert repeated_score > single_score


def test_exact_keyword_phrase_receives_bonus():
    exact_phrase_chunk = {
        "document_title": "Security Policy",
        "content": (
            "Remote work policy requirements "
            "apply to all employees."
        ),
    }

    separated_keywords_chunk = {
        "document_title": "Security Policy",
        "content": (
            "Remote employees must follow the "
            "company policy when performing work."
        ),
    }

    keywords = [
        "remote",
        "work",
        "policy",
    ]

    exact_score = calculate_chunk_relevance_score(
        chunk=exact_phrase_chunk,
        keywords=keywords,
        original_question="What is the remote work policy?",
    )

    separated_score = calculate_chunk_relevance_score(
        chunk=separated_keywords_chunk,
        keywords=keywords,
        original_question="What is the remote work policy?",
    )

    assert exact_score > separated_score


@pytest.mark.asyncio
async def test_search_chunks_removes_candidates_below_threshold(
    monkeypatch,
):
    candidates = [
        {
            "id": "strong-chunk",
            "document_id": "document-1",
            "chunk_index": 0,
            "document_title": "MFA Policy",
            "category": "Security",
            "content": "MFA is mandatory for all employees.",
        },
        {
            "id": "weak-chunk",
            "document_id": "document-2",
            "chunk_index": 0,
            "document_title": "Company Information",
            "category": "Security",
            "content": (
                "This document contains general "
                "company information."
            ),
        },
    ]

    async def fake_search_chunk_candidates(
        keywords,
        category=None,
        limit=50,
    ):
        return candidates

    monkeypatch.setattr(
        search_repository,
        "search_chunk_candidates",
        fake_search_chunk_candidates,
    )

    monkeypatch.setattr(
        search_repository.settings,
        "retrieval_min_score",
        8,
    )

    result = await search_repository.search_chunks(
        question="Is MFA mandatory?",
        category="Security",
        limit=5,
    )

    assert len(result) == 1
    assert result[0]["id"] == "strong-chunk"


@pytest.mark.asyncio
async def test_search_chunks_respects_configurable_limit(
    monkeypatch,
):
    candidates = [
        {
            "id": f"chunk-{index}",
            "document_id": f"document-{index}",
            "chunk_index": 0,
            "document_title": "Security Policy",
            "category": "Security",
            "content": "MFA is mandatory for all employees.",
        }
        for index in range(5)
    ]

    async def fake_search_chunk_candidates(
        keywords,
        category=None,
        limit=50,
    ):
        return candidates

    monkeypatch.setattr(
        search_repository,
        "search_chunk_candidates",
        fake_search_chunk_candidates,
    )

    monkeypatch.setattr(
        search_repository.settings,
        "retrieval_min_score",
        1,
    )

    result = await search_repository.search_chunks(
        question="Is MFA mandatory?",
        category="Security",
        limit=2,
    )

    assert len(result) == 2
