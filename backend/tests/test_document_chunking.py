import pytest

from app.services.document_chunking_service import (
    DocumentChunkingError,
    chunk_document_text,
    normalize_document_text,
)


def test_normalize_document_text_removes_extra_whitespace() -> None:
    text = "First   line.\n\n\nSecond\tline."

    result = normalize_document_text(text)

    assert result == "First line.\n\nSecond line."


def test_normalize_document_text_rejects_empty_content() -> None:
    with pytest.raises(
        DocumentChunkingError,
        match="Document content cannot be empty",
    ):
        normalize_document_text("   ")


def test_short_document_returns_one_chunk() -> None:
    text = "Employees must use multi-factor authentication."

    chunks = chunk_document_text(
        text=text,
        chunk_size=100,
        chunk_overlap=20,
    )

    assert len(chunks) == 1
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["content"] == text
    assert chunks[0]["start_character"] == 0
    assert chunks[0]["end_character"] == len(text)


def test_long_document_returns_multiple_chunks() -> None:
    text = " ".join(
        f"Sentence number {index}."
        for index in range(100)
    )

    chunks = chunk_document_text(
        text=text,
        chunk_size=200,
        chunk_overlap=40,
    )

    assert len(chunks) > 1
    assert [chunk["chunk_index"] for chunk in chunks] == list(
        range(len(chunks))
    )


def test_chunks_overlap() -> None:
    text = " ".join(
        f"Policy sentence {index}."
        for index in range(60)
    )

    chunks = chunk_document_text(
        text=text,
        chunk_size=160,
        chunk_overlap=30,
    )

    assert len(chunks) > 1
    assert chunks[1]["start_character"] < chunks[0]["end_character"]


def test_chunk_metadata_is_consistent() -> None:
    text = " ".join(
        f"Security rule {index}."
        for index in range(50)
    )

    chunks = chunk_document_text(
        text=text,
        chunk_size=150,
        chunk_overlap=25,
    )

    for chunk in chunks:
        content = chunk["content"]

        assert chunk["character_count"] == len(content)
        assert chunk["start_character"] < chunk["end_character"]
        assert content


@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap", "expected_message"),
    [
        (0, 0, "Chunk size must be greater than zero"),
        (-1, 0, "Chunk size must be greater than zero"),
        (100, -1, "Chunk overlap cannot be negative"),
        (100, 100, "Chunk overlap must be smaller than chunk size"),
        (100, 120, "Chunk overlap must be smaller than chunk size"),
    ],
)
def test_invalid_chunk_configuration(
    chunk_size: int,
    chunk_overlap: int,
    expected_message: str,
) -> None:
    with pytest.raises(
        DocumentChunkingError,
        match=expected_message,
    ):
        chunk_document_text(
            text="Valid document content.",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )