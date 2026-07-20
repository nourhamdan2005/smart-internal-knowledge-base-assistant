from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from qdrant_client.http import models

from app.core.config import Settings
from app.vectorstores.base import (
    VectorStoreConfigurationError,
    VectorValidationError,
)
from app.vectorstores.qdrant_store import (
    QdrantVectorStore,
    deterministic_point_id,
)


def make_store(client, **overrides):
    configuration = Settings(
        _env_file=None,
        qdrant_vector_size=2,
        qdrant_batch_size=2,
        **overrides,
    )
    return QdrantVectorStore(configuration, client=client)


def make_point(chunk_id="chunk-1", embedding=None):
    from app.vectorstores.base import VectorPoint

    return VectorPoint(
        chunk_id=chunk_id,
        document_id="document-1",
        embedding=embedding or [1.0, 0.0],
        content="Employees must use MFA.",
        title="Security Policy",
        category="Security",
        chunk_index=0,
        is_active=True,
        embedding_model="nomic-embed-text",
        embedding_dimensions=len(embedding or [1.0, 0.0]),
    )


@pytest.mark.asyncio
async def test_initialize_creates_missing_collection():
    client = SimpleNamespace(
        collection_exists=AsyncMock(return_value=False),
        create_collection=AsyncMock(),
        create_payload_index=AsyncMock(),
    )
    store = make_store(client)

    await store.initialize()

    client.create_collection.assert_awaited_once()
    assert client.create_payload_index.await_count == 5


@pytest.mark.asyncio
async def test_initialize_keeps_compatible_collection():
    vectors = models.VectorParams(
        size=2,
        distance=models.Distance.COSINE,
    )
    client = SimpleNamespace(
        collection_exists=AsyncMock(return_value=True),
        get_collection=AsyncMock(
            return_value=SimpleNamespace(
                config=SimpleNamespace(
                    params=SimpleNamespace(vectors=vectors)
                )
            )
        ),
        create_collection=AsyncMock(),
        create_payload_index=AsyncMock(),
    )

    await make_store(client).initialize()

    client.create_collection.assert_not_awaited()


@pytest.mark.asyncio
async def test_initialize_rejects_incompatible_dimensions():
    vectors = models.VectorParams(
        size=3,
        distance=models.Distance.COSINE,
    )
    client = SimpleNamespace(
        collection_exists=AsyncMock(return_value=True),
        get_collection=AsyncMock(
            return_value=SimpleNamespace(
                config=SimpleNamespace(
                    params=SimpleNamespace(vectors=vectors)
                )
            )
        ),
    )

    with pytest.raises(VectorStoreConfigurationError):
        await make_store(client).initialize()


def test_deterministic_point_id_is_stable_uuid():
    first = deterministic_point_id("chunk-1")
    second = deterministic_point_id("chunk-1")

    assert first == second
    assert first != deterministic_point_id("chunk-2")
    assert len(first) == 36


def test_point_conversion_preserves_required_payload():
    store = make_store(SimpleNamespace())

    point = store._point_struct(make_point())

    assert point.id == deterministic_point_id("chunk-1")
    assert point.vector == [1.0, 0.0]
    assert point.payload["chunk_id"] == "chunk-1"
    assert point.payload["is_active"] is True


def test_point_conversion_rejects_wrong_dimensions():
    store = make_store(SimpleNamespace())

    with pytest.raises(VectorValidationError):
        store._point_struct(make_point(embedding=[1.0]))


@pytest.mark.asyncio
async def test_upsert_chunks_uses_configured_batches():
    client = SimpleNamespace(upsert=AsyncMock())
    store = make_store(client)
    points = [make_point(f"chunk-{index}") for index in range(3)]

    stats = await store.upsert_chunks(points)

    assert stats.processed == 3
    assert stats.batches == 2
    assert client.upsert.await_count == 2


@pytest.mark.asyncio
async def test_search_applies_active_category_and_document_filters():
    response = SimpleNamespace(
        points=[
            SimpleNamespace(
                score=0.91,
                payload={
                    "chunk_id": "chunk-1",
                    "document_id": "document-1",
                },
            )
        ]
    )
    client = SimpleNamespace(query_points=AsyncMock(return_value=response))
    store = make_store(client)

    results = await store.search(
        [1.0, 0.0],
        limit=5,
        category="Security",
        document_ids=["document-1"],
    )

    assert results[0].chunk_id == "chunk-1"
    assert results[0].score == pytest.approx(0.91)
    query_filter = client.query_points.await_args.kwargs[
        "query_filter"
    ]
    assert len(query_filter.must) == 3


@pytest.mark.asyncio
async def test_delete_by_chunk_ids_uses_deterministic_ids():
    client = SimpleNamespace(delete=AsyncMock())
    store = make_store(client)

    deleted = await store.delete_by_chunk_ids(
        ["chunk-1", "chunk-1"]
    )

    assert deleted == 1
    selector = client.delete.await_args.kwargs["points_selector"]
    assert selector.points == [deterministic_point_id("chunk-1")]


@pytest.mark.asyncio
async def test_delete_by_document_id_is_idempotent():
    client = SimpleNamespace(
        count=AsyncMock(return_value=SimpleNamespace(count=0)),
        delete=AsyncMock(),
    )
    store = make_store(client)

    assert await store.delete_by_document_id("document-1") == 0
    client.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_health_check_returns_false_on_provider_failure():
    client = SimpleNamespace(
        collection_exists=AsyncMock(side_effect=TimeoutError())
    )

    assert await make_store(client).health_check() is False
