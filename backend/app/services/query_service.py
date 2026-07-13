from app.ai.openai_client import generate_answer
from app.repositories.search_repository import search_chunks


async def query_documents(
    question: str,
    category: str | None = None,
):
    chunks = await search_chunks(
        question=question,
        category=category,
        limit=8,
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
        }
        for chunk in chunks
    ]

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
    }