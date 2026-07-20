import pytest

from app.ai import embedding_client


@pytest.mark.asyncio
async def test_generate_embedding_returns_vector(
    monkeypatch,
):
    async def fake_embeddings(
        model,
        prompt,
    ):
        return {
            "embedding": [
                0.1,
                0.2,
                0.3,
            ]
        }

    monkeypatch.setattr(
        embedding_client.client,
        "embeddings",
        fake_embeddings,
    )

    result = await embedding_client.generate_embedding(
        "Hello world"
    )

    assert result == [
        0.1,
        0.2,
        0.3,
    ]


@pytest.mark.asyncio
async def test_generate_embedding_rejects_blank_text():
    with pytest.raises(ValueError):
        await embedding_client.generate_embedding("   ")


@pytest.mark.asyncio
async def test_generate_embedding_rejects_missing_vector(
    monkeypatch,
):
    async def fake_embeddings(
        model,
        prompt,
    ):
        return {}

    monkeypatch.setattr(
        embedding_client.client,
        "embeddings",
        fake_embeddings,
    )

    with pytest.raises(RuntimeError):
        await embedding_client.generate_embedding(
            "Hello"
        )