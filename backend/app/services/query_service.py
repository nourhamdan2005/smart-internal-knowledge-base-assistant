import re

from app.ai.openai_client import generate_answer
from app.core.config import settings
from app.repositories.search_repository import (
    hybrid_search_chunks,
)


SOURCE_EXCERPT_LENGTH = 180


def create_source_excerpt(
    content: str,
    max_length: int = SOURCE_EXCERPT_LENGTH,
) -> str:
    """
    Create a clean, shortened excerpt for a query source.
    """
    normalized_content = re.sub(
        r"\s+",
        " ",
        content,
    ).strip()

    if len(normalized_content) <= max_length:
        return normalized_content

    shortened_content = normalized_content[
        :max_length
    ].rstrip()

    last_space = shortened_content.rfind(" ")

    if last_space > 0:
        shortened_content = shortened_content[
            :last_space
        ]

    return f"{shortened_content}..."


async def query_documents(
    question: str,
    category: str | None = None,
):
    chunks = await hybrid_search_chunks(
        question=question,
        category=category,
        limit=settings.retrieval_top_k,
    )

    if not chunks:
        return {
            "question": question,
            "answer": (
                "I couldn't find this information "
                "in the available documents."
            ),
            "sources": [],
        }

    context = "\n\n".join(
        (
            f"Source {position}\n"
            f"Document: {chunk['document_title']}\n"
            f"Category: {chunk['category']}\n"
            f"Chunk: {chunk['chunk_index']}\n"
            f"Content: {chunk['content']}"
        )
        for position, chunk in enumerate(
            chunks,
            start=1,
        )
    )

    answer = await generate_answer(
        question=question,
        context=context,
    )

    sources = [
        {
            "chunk_id": chunk["id"],
            "chunk_index": chunk["chunk_index"],
            "document_id": chunk["document_id"],
            "title": chunk["document_title"],
            "category": chunk["category"],
            "excerpt": create_source_excerpt(
                chunk["content"]
            ),
        }
        for chunk in chunks
    ]

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
    }
