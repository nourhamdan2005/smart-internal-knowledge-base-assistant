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
        embedding_client.ollama_client,
        "embeddings",
        fake_embeddings,
    )
    monkeypatch.setattr(
        embedding_client.settings,
        "embedding_provider",
        "ollama",
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
        embedding_client.ollama_client,
        "embeddings",
        fake_embeddings,
    )
    monkeypatch.setattr(
        embedding_client.settings,
        "embedding_provider",
        "ollama",
    )

    with pytest.raises(RuntimeError):
        await embedding_client.generate_embedding(
            "Hello"
        )


@pytest.mark.asyncio
async def test_generate_embedding_with_gemini(monkeypatch):
    class FakeEmbedding:
        values = [0.1, 0.2, 0.3]

    class FakeResponse:
        embeddings = [FakeEmbedding()]

    async def fake_embed_content(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        embedding_client.settings,
        "embedding_provider",
        "gemini",
    )

    monkeypatch.setattr(
        embedding_client,
        "gemini_client",
        object(),
    )

    class FakeModels:
        embed_content = fake_embed_content

    class FakeAio:
        models = FakeModels()

    class FakeGeminiClient:
        aio = FakeAio()

    monkeypatch.setattr(
        embedding_client,
        "gemini_client",
        FakeGeminiClient(),
    )

    result = await embedding_client.generate_embedding(
        "Remote work policy"
    )

    assert result == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_generate_embedding_gemini_requires_api_key(
    monkeypatch,
):
    monkeypatch.setattr(
        embedding_client.settings,
        "embedding_provider",
        "gemini",
    )

    monkeypatch.setattr(
        embedding_client,
        "gemini_client",
        None,
    )

    with pytest.raises(
        RuntimeError,
        match="GEMINI_API_KEY",
    ):
        await embedding_client.generate_embedding(
            "Remote work policy"
        )


@pytest.mark.asyncio
async def test_generate_embedding_gemini_rejects_empty_vector(
    monkeypatch,
):
    class FakeEmbedding:
        values = []

    class FakeResponse:
        embeddings = [FakeEmbedding()]

    async def fake_embed_content(*args, **kwargs):
        return FakeResponse()

    class FakeModels:
        embed_content = fake_embed_content

    class FakeAio:
        models = FakeModels()

    class FakeGeminiClient:
        aio = FakeAio()

    monkeypatch.setattr(
        embedding_client.settings,
        "embedding_provider",
        "gemini",
    )

    monkeypatch.setattr(
        embedding_client,
        "gemini_client",
        FakeGeminiClient(),
    )

    with pytest.raises(
        RuntimeError,
        match="empty embedding",
    ):
        await embedding_client.generate_embedding(
            "Remote work policy"
        )
