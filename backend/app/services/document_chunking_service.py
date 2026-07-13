import re


DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200


class DocumentChunkingError(Exception):
    """Raised when document content cannot be chunked."""


def normalize_document_text(text: str) -> str:
    """
    Normalize whitespace while preserving paragraph boundaries.
    """
    if not text or not text.strip():
        raise DocumentChunkingError(
            "Document content cannot be empty."
        )

    normalized_lines: list[str] = []

    for line in text.splitlines():
        cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
        normalized_lines.append(cleaned_line)

    normalized_text = "\n".join(normalized_lines)

    normalized_text = re.sub(
        r"\n{3,}",
        "\n\n",
        normalized_text,
    )

    return normalized_text.strip()


def find_chunk_end(
    text: str,
    start: int,
    target_end: int,
) -> int:
    """
    Prefer ending a chunk at a paragraph, sentence, or word boundary.
    """
    if target_end >= len(text):
        return len(text)

    search_start = start + max(
        1,
        int((target_end - start) * 0.6),
    )

    boundaries = [
        text.rfind("\n\n", search_start, target_end),
        text.rfind(". ", search_start, target_end),
        text.rfind("! ", search_start, target_end),
        text.rfind("? ", search_start, target_end),
        text.rfind(" ", search_start, target_end),
    ]

    best_boundary = max(boundaries)

    if best_boundary <= start:
        return target_end

    boundary_text = text[best_boundary:best_boundary + 2]

    if boundary_text in {". ", "! ", "? "}:
        return best_boundary + 1

    return best_boundary


def chunk_document_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict[str, int | str]]:
    """
    Split document text into overlapping chunks.

    Each chunk contains:
    - chunk_index
    - content
    - start_character
    - end_character
    - character_count
    """
    if chunk_size <= 0:
        raise DocumentChunkingError(
            "Chunk size must be greater than zero."
        )

    if chunk_overlap < 0:
        raise DocumentChunkingError(
            "Chunk overlap cannot be negative."
        )

    if chunk_overlap >= chunk_size:
        raise DocumentChunkingError(
            "Chunk overlap must be smaller than chunk size."
        )

    normalized_text = normalize_document_text(text)

    chunks: list[dict[str, int | str]] = []
    start = 0
    chunk_index = 0
    text_length = len(normalized_text)

    while start < text_length:
        target_end = min(
            start + chunk_size,
            text_length,
        )

        end = find_chunk_end(
            text=normalized_text,
            start=start,
            target_end=target_end,
        )

        chunk_content = normalized_text[start:end].strip()

        if chunk_content:
            chunks.append(
                {
                    "chunk_index": chunk_index,
                    "content": chunk_content,
                    "start_character": start,
                    "end_character": end,
                    "character_count": len(chunk_content),
                }
            )
            chunk_index += 1

        if end >= text_length:
            break

        next_start = max(
            end - chunk_overlap,
            start + 1,
        )

        while (
            next_start < text_length
            and normalized_text[next_start].isspace()
        ):
            next_start += 1

        start = next_start

    return chunks