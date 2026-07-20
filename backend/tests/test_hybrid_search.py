import pytest

from app.repositories import search_repository
from app.repositories.search_repository import (
    calculate_cosine_similarity,
    calculate_hybrid_score,
    merge_chunk_candidates,
    normalize_keyword_score,
)


def make_chunk(
    chunk_id: str,
    document_id: str,
    content: str,
    embedding: list[float],
    title: str = "Company Policy",
) -> dict:
    return {
        "id": chunk_id,
        "document_id": document_id,
        "chunk_index": 0,
        "document_title": title,
        "category": "IT",
        "content": content,
        "embedding": embedding,
        "embedding_model": "nomic-embed-text",
        "embedding_dimensions": len(embedding),
        "start_character": 0,
        "end_character": len(content),
    }


def test_cosine_similarity_for_identical_vectors():
    result = calculate_cosine_similarity(
        [1.0, 0.0],
        [1.0, 0.0],
    )

    assert result == pytest.approx(1.0)


def test_cosine_similarity_for_opposite_vectors():
    result = calculate_cosine_similarity(
        [1.0, 0.0],
        [-1.0, 0.0],
    )

    assert result == pytest.approx(-1.0)


def test_cosine_similarity_rejects_dimension_mismatch():
    result = calculate_cosine_similarity(
        [1.0, 0.0],
        [1.0, 0.0, 0.0],
    )

    assert result == 0.0


def test_normalize_keyword_score_is_bounded():
    assert normalize_keyword_score(0) == 0.0
    assert normalize_keyword_score(50) == 0.5
    assert normalize_keyword_score(200) == 1.0


def test_hybrid_score_uses_both_components(
    monkeypatch,
):
    monkeypatch.setattr(
        search_repository.settings,
        "hybrid_keyword_weight",
        0.4,
    )

    monkeypatch.setattr(
        search_repository.settings,
        "hybrid_semantic_weight",
        0.6,
    )

    result = calculate_hybrid_score(
        keyword_score=50,
        semantic_similarity=0.8,
    )

    assert result == pytest.approx(0.68)


def test_merge_chunk_candidates_removes_duplicates():
    keyword_chunk = make_chunk(
        chunk_id="chunk-1",
        document_id="document-1",
        content="MFA is mandatory.",
        embedding=[],
    )

    semantic_chunk = {
        **keyword_chunk,
        "embedding": [1.0, 0.0],
        "embedding_dimensions": 2,
    }

    result = merge_chunk_candidates(
        keyword_candidates=[keyword_chunk],
        semantic_candidates=[semantic_chunk],
    )

    assert len(result) == 1
    assert result[0]["embedding"] == [
        1.0,
        0.0,
    ]


@pytest.mark.asyncio
async def test_hybrid_search_finds_semantic_only_match(
    monkeypatch,
):
    semantic_chunk = make_chunk(
        chunk_id="chunk-semantic",
        document_id="document-1",
        content=(
            "Multi-factor authentication is "
            "mandatory for every account."
        ),
        embedding=[1.0, 0.0],
        title="Security Policy",
    )

    async def fake_keyword_candidates(
        keywords,
        category=None,
        limit=50,
    ):
        return []

    async def fake_generate_embedding(text):
        assert text == (
            "Do I need an extra login "
            "verification step?"
        )

        return [1.0, 0.0]

    async def fake_semantic_candidates(
        category=None,
        limit=100,
    ):
        return [semantic_chunk]

    monkeypatch.setattr(
        search_repository,
        "search_chunk_candidates",
        fake_keyword_candidates,
    )

    monkeypatch.setattr(
        search_repository,
        "generate_embedding",
        fake_generate_embedding,
    )

    monkeypatch.setattr(
        search_repository,
        "get_active_chunks_with_embeddings",
        fake_semantic_candidates,
    )

    monkeypatch.setattr(
        search_repository.settings,
        "semantic_min_similarity",
        0.25,
    )

    result = await (
        search_repository.hybrid_search_chunks(
            question=(
                "Do I need an extra login "
                "verification step?"
            ),
            category="IT",
            limit=5,
        )
    )

    assert len(result) == 1
    assert result[0]["id"] == (
        "chunk-semantic"
    )
    assert result[0]["semantic_similarity"] == (
        pytest.approx(1.0)
    )


@pytest.mark.asyncio
async def test_hybrid_search_ranks_semantic_match_first(
    monkeypatch,
):
    strong_chunk = make_chunk(
        chunk_id="strong",
        document_id="document-1",
        content="Additional account verification.",
        embedding=[1.0, 0.0],
    )

    weak_chunk = make_chunk(
        chunk_id="weak",
        document_id="document-2",
        content="General company information.",
        embedding=[0.0, 1.0],
    )

    async def fake_keyword_candidates(
        keywords,
        category=None,
        limit=50,
    ):
        return [
            weak_chunk,
            strong_chunk,
        ]

    async def fake_generate_embedding(text):
        return [1.0, 0.0]

    async def fake_semantic_candidates(
        category=None,
        limit=100,
    ):
        return [
            strong_chunk,
            weak_chunk,
        ]

    monkeypatch.setattr(
        search_repository,
        "search_chunk_candidates",
        fake_keyword_candidates,
    )

    monkeypatch.setattr(
        search_repository,
        "generate_embedding",
        fake_generate_embedding,
    )

    monkeypatch.setattr(
        search_repository,
        "get_active_chunks_with_embeddings",
        fake_semantic_candidates,
    )

    monkeypatch.setattr(
        search_repository.settings,
        "retrieval_min_score",
        0,
    )

    monkeypatch.setattr(
        search_repository.settings,
        "semantic_min_similarity",
        0.0,
    )

    result = await (
        search_repository.hybrid_search_chunks(
            question="Extra account verification",
            category="IT",
            limit=2,
        )
    )

    assert result[0]["id"] == "strong"


@pytest.mark.asyncio
async def test_hybrid_search_falls_back_to_keywords(
    monkeypatch,
):
    keyword_result = [
        make_chunk(
            chunk_id="keyword-chunk",
            document_id="document-1",
            content="VPN access policy.",
            embedding=[],
        )
    ]

    async def fake_generate_embedding(text):
        raise RuntimeError(
            "Embedding service unavailable"
        )

    async def fake_keyword_search(
        question,
        category=None,
        limit=None,
    ):
        return keyword_result

    async def fake_keyword_candidates(
        keywords,
        category=None,
        limit=50,
    ):
        return keyword_result

    monkeypatch.setattr(
        search_repository,
        "generate_embedding",
        fake_generate_embedding,
    )

    monkeypatch.setattr(
        search_repository,
        "search_chunks",
        fake_keyword_search,
    )

    monkeypatch.setattr(
        search_repository,
        "search_chunk_candidates",
        fake_keyword_candidates,
    )

    result = await (
        search_repository.hybrid_search_chunks(
            question="VPN access",
            category="IT",
            limit=5,
        )
    )

    assert result == keyword_result


@pytest.mark.asyncio
async def test_hybrid_search_filters_weak_candidates(
    monkeypatch,
):
    weak_chunk = make_chunk(
        chunk_id="weak",
        document_id="document-1",
        content="Unrelated information.",
        embedding=[0.0, 1.0],
    )

    async def fake_keyword_candidates(
        keywords,
        category=None,
        limit=50,
    ):
        return [weak_chunk]

    async def fake_generate_embedding(text):
        return [1.0, 0.0]

    async def fake_semantic_candidates(
        category=None,
        limit=100,
    ):
        return [weak_chunk]

    monkeypatch.setattr(
        search_repository,
        "search_chunk_candidates",
        fake_keyword_candidates,
    )

    monkeypatch.setattr(
        search_repository,
        "generate_embedding",
        fake_generate_embedding,
    )

    monkeypatch.setattr(
        search_repository,
        "get_active_chunks_with_embeddings",
        fake_semantic_candidates,
    )

    monkeypatch.setattr(
        search_repository.settings,
        "retrieval_min_score",
        8,
    )

    monkeypatch.setattr(
        search_repository.settings,
        "semantic_min_similarity",
        0.25,
    )

    result = await (
        search_repository.hybrid_search_chunks(
            question="MFA requirement",
            category="IT",
            limit=5,
        )
    )

    assert result == []