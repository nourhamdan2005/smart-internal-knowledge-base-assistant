import re

from app.ai.openai_client import generate_answer
from app.core.config import settings
from app.core.query_profiling import get_query_profiler
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
    prepared = await prepare_query(question, category)
    if not prepared["chunks"]:
        return prepared["fallback_response"]

    context = prepared["context"]
    profiler = get_query_profiler()
    if profiler:
        try:
            async with profiler.stage("llm_generation_ms"):
                answer = await generate_answer(question=question, context=context)
        except Exception:
            profiler.set(ollama_failed=True)
            raise
        profiler.set(answer_character_count=len(answer))
    else:
        answer = await generate_answer(question=question, context=context)

    return {"question": question, "answer": answer, "sources": prepared["sources"]}


async def prepare_query(question: str, category: str | None = None) -> dict:
    """Retrieve context and build the established public source contract."""
    chunks = await hybrid_search_chunks(
        question=question,
        category=category,
        limit=settings.retrieval_top_k,
    )

    if not chunks:
        fallback_response = {
            "question": question,
            "answer": (
                "I couldn't find this information "
                "in the available documents."
            ),
            "sources": [],
        }
        return {"chunks": [], "context": "", "sources": [], "fallback_response": fallback_response}

    profiler = get_query_profiler()
    timer = profiler.stage("prompt_build_ms") if profiler else None
    if timer:
        timer.__enter__()
    try:
        context = "\n\n".join(
            (
                f"Source {position}\n"
                f"Document: {chunk['document_title']}\n"
                f"Category: {chunk['category']}\n"
                f"Chunk: {chunk['chunk_index']}\n"
                f"Content: {chunk['content']}"
            )
            for position, chunk in enumerate(chunks, start=1)
        )
    finally:
        if timer:
            timer.__exit__(None, None, None)

    if profiler:
        profiler.set(
            final_context_chunks=len(chunks),
            prompt_character_count=len(context) + len(question),
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

    return {"chunks": chunks, "context": context, "sources": sources, "fallback_response": None}
