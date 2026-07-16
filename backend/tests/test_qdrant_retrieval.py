import pytest

from app.repositories import search_repository
from app.vectorstores.base import (
    VectorSearchResult,
    VectorStoreUnavailableError,
)


def make_chunk(
    chunk_id="chunk-1",
    content="Multi-factor authentication is mandatory.",
):
    return {
        "id": chunk_id,
        "document_id": "document-1",
        "chunk_index": 0,
        "document_title": "Security Policy",
        "category": "Security",
        "content": content,
        "embedding": [1.0, 0.0],
        "embedding_model": "nomic-embed-text",
        "embedding_dimensions": 2,
        "is_active": True,
    }


@pytest.mark.asyncio
async def test_qdrant_candidates_are_hydrated_from_mongodb(
    monkeypatch,
):
    chunk = make_chunk()

    class Store:
        async def search(
            self,
            embedding,
            limit,
            category=None,
            document_ids=None,
        ):
            assert category == "Security"
            return [
                VectorSearchResult(
                    chunk_id="chunk-1",
                    document_id="document-1",
                    score=0.92,
                )
            ]

    async def fake_embedding(text):
        return [1.0, 0.0]

    async def fake_keywords(keywords, category=None, limit=50):
        assert category == "Security"
        return []

    async def fake_hydrate(chunk_ids, category=None):
        assert chunk_ids == ["chunk-1"]
        assert category == "Security"
        return [chunk]

    async def forbidden_scan(*args, **kwargs):
        raise AssertionError("Python semantic scan must not run")

    monkeypatch.setattr(
        search_repository.settings,
        "qdrant_enabled",
        True,
    )
    monkeypatch.setattr(
        search_repository,
        "get_vector_store",
        lambda: Store(),
    )
    monkeypatch.setattr(
        search_repository,
        "generate_embedding",
        fake_embedding,
    )
    monkeypatch.setattr(
        search_repository,
        "search_chunk_candidates",
        fake_keywords,
    )
    monkeypatch.setattr(
        search_repository,
        "get_active_chunks_by_ids",
        fake_hydrate,
    )
    monkeypatch.setattr(
        search_repository,
        "get_active_chunks_with_embeddings",
        forbidden_scan,
    )

    result = await search_repository.hybrid_search_chunks(
        "extra login verification",
        category="Security",
    )

    assert result[0]["id"] == "chunk-1"
    assert result[0]["semantic_similarity"] == pytest.approx(0.92)


@pytest.mark.asyncio
async def test_inactive_qdrant_results_are_rejected(monkeypatch):
    class Store:
        async def search(self, **kwargs):
            return [
                VectorSearchResult(
                    chunk_id="stale",
                    document_id="deleted-document",
                    score=1.0,
                )
            ]

    async def empty_keywords(**kwargs):
        return []

    async def no_active_chunks(chunk_ids, category=None):
        return []

    async def fake_embedding(text):
        return [1.0, 0.0]

    monkeypatch.setattr(
        search_repository.settings,
        "qdrant_enabled",
        True,
    )
    monkeypatch.setattr(
        search_repository,
        "get_vector_store",
        lambda: Store(),
    )
    monkeypatch.setattr(
        search_repository,
        "generate_embedding",
        fake_embedding,
    )
    monkeypatch.setattr(
        search_repository,
        "search_chunk_candidates",
        empty_keywords,
    )
    monkeypatch.setattr(
        search_repository,
        "get_active_chunks_by_ids",
        no_active_chunks,
    )

    assert await search_repository.hybrid_search_chunks("MFA") == []


@pytest.mark.asyncio
async def test_duplicate_qdrant_results_are_deduplicated(monkeypatch):
    class Store:
        async def search(self, **kwargs):
            return [
                VectorSearchResult("chunk-1", "document-1", 0.8),
                VectorSearchResult("chunk-1", "document-1", 0.9),
            ]

    async def empty_keywords(**kwargs):
        return []

    async def fake_hydrate(chunk_ids, category=None):
        assert chunk_ids == ["chunk-1"]
        return [make_chunk()]

    async def fake_embedding(text):
        return [1.0, 0.0]

    monkeypatch.setattr(search_repository.settings, "qdrant_enabled", True)
    monkeypatch.setattr(search_repository, "get_vector_store", lambda: Store())
    monkeypatch.setattr(search_repository, "generate_embedding", fake_embedding)
    monkeypatch.setattr(search_repository, "search_chunk_candidates", empty_keywords)
    monkeypatch.setattr(search_repository, "get_active_chunks_by_ids", fake_hydrate)

    result = await search_repository.hybrid_search_chunks("MFA")

    assert len(result) == 1
    assert result[0]["semantic_similarity"] == pytest.approx(0.9)


@pytest.mark.parametrize(
    "provider_error",
    [
        VectorStoreUnavailableError("offline"),
        TimeoutError("timed out"),
        ConnectionError("refused"),
    ],
)
@pytest.mark.asyncio
async def test_qdrant_failure_uses_python_semantic_fallback(
    monkeypatch,
    provider_error,
):
    chunk = make_chunk()

    class Store:
        async def search(self, **kwargs):
            raise provider_error

    async def empty_keywords(**kwargs):
        return []

    async def local_chunks(**kwargs):
        return [chunk]

    async def fake_embedding(text):
        return [1.0, 0.0]

    monkeypatch.setattr(search_repository.settings, "qdrant_enabled", True)
    monkeypatch.setattr(
        search_repository.settings,
        "qdrant_fallback_enabled",
        True,
    )
    monkeypatch.setattr(search_repository, "get_vector_store", lambda: Store())
    monkeypatch.setattr(search_repository, "generate_embedding", fake_embedding)
    monkeypatch.setattr(search_repository, "search_chunk_candidates", empty_keywords)
    monkeypatch.setattr(
        search_repository,
        "get_active_chunks_with_embeddings",
        local_chunks,
    )

    result = await search_repository.hybrid_search_chunks("MFA")

    assert result[0]["id"] == "chunk-1"


@pytest.mark.asyncio
async def test_qdrant_failure_is_controlled_when_fallback_disabled(
    monkeypatch,
):
    class Store:
        async def search(self, **kwargs):
            raise VectorStoreUnavailableError("offline")

    async def empty_keywords(**kwargs):
        return []

    async def fake_embedding(text):
        return [1.0, 0.0]

    monkeypatch.setattr(search_repository.settings, "qdrant_enabled", True)
    monkeypatch.setattr(
        search_repository.settings,
        "qdrant_fallback_enabled",
        False,
    )
    monkeypatch.setattr(search_repository, "get_vector_store", lambda: Store())
    monkeypatch.setattr(search_repository, "generate_embedding", fake_embedding)
    monkeypatch.setattr(search_repository, "search_chunk_candidates", empty_keywords)

    with pytest.raises(VectorStoreUnavailableError):
        await search_repository.hybrid_search_chunks("MFA")


@pytest.mark.asyncio
async def test_empty_semantic_results_keep_keyword_candidates(monkeypatch):
    keyword_chunk = make_chunk(content="VPN access policy for employees.")

    class Store:
        async def search(self, **kwargs):
            return []

    async def keyword_chunks(**kwargs):
        return [keyword_chunk]

    async def fake_hydrate(chunk_ids, category=None):
        return []

    async def fake_embedding(text):
        return [1.0, 0.0]

    monkeypatch.setattr(search_repository.settings, "qdrant_enabled", True)
    monkeypatch.setattr(search_repository, "get_vector_store", lambda: Store())
    monkeypatch.setattr(search_repository, "generate_embedding", fake_embedding)
    monkeypatch.setattr(search_repository, "search_chunk_candidates", keyword_chunks)
    monkeypatch.setattr(search_repository, "get_active_chunks_by_ids", fake_hydrate)

    result = await search_repository.hybrid_search_chunks("VPN access policy")

    assert result[0]["id"] == "chunk-1"
