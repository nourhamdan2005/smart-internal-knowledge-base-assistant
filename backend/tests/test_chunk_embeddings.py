import pytest

from app.services import document_chunk_service


@pytest.mark.asyncio
async def test_create_chunks_generates_embeddings(
    monkeypatch,
):
    monkeypatch.setattr(
        document_chunk_service.settings,
        "embedding_model",
        "nomic-embed-text",
    )

    document = {
        "id": "doc-1",
        "title": "Security Policy",
        "category": "Security",
        "content": (
            "Employees must use MFA."
        ),
    }

    async def fake_embedding(
        text,
    ):
        return [0.1, 0.2, 0.3]

    stored_chunks = []

    async def fake_create_document_chunks(
        chunks,
    ):
        stored_chunks.extend(chunks)

        return [
            chunk.model_dump()
            for chunk in chunks
        ]

    monkeypatch.setattr(
        document_chunk_service,
        "generate_embedding",
        fake_embedding,
    )

    monkeypatch.setattr(
        document_chunk_service,
        "create_document_chunks",
        fake_create_document_chunks,
    )

    await document_chunk_service.create_chunks_for_document(
        document
    )

    assert stored_chunks

    for chunk in stored_chunks:
        assert chunk.embedding == [
            0.1,
            0.2,
            0.3,
        ]

        assert (
            chunk.embedding_model
            == "nomic-embed-text"
        )

        assert (
            chunk.embedding_dimensions
            == 3
        )


@pytest.mark.asyncio
async def test_embedding_failure_stops_chunk_creation(
    monkeypatch,
):
    document = {
        "id": "doc-1",
        "title": "Security Policy",
        "category": "Security",
        "content": (
            "Employees must use MFA."
        ),
    }

    async def fake_embedding(
        text,
    ):
        raise RuntimeError(
            "Embedding failed"
        )

    monkeypatch.setattr(
        document_chunk_service,
        "generate_embedding",
        fake_embedding,
    )

    with pytest.raises(
        RuntimeError,
        match="Embedding failed",
    ):
        await (
            document_chunk_service
            .create_chunks_for_document(
                document
            )
        )
