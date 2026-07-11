from app.ai.openai_client import generate_answer
from app.repositories.document_repository import get_documents


async def query_documents(question: str, category: str | None = None):
    documents = await get_documents(
        category=category,
        search=question,
        page=1,
        limit=5,
        sort="-created_at",
    )

    if not documents:
        return {
            "question": question,
            "answer": "I couldn't find this information in the available documents.",
            "sources": [],
        }

    context = "\n\n".join(
        f"Title: {doc['title']}\n"
        f"Category: {doc['category']}\n"
        f"Content: {doc['content']}"
        for doc in documents
    )

    answer = await generate_answer(
        question=question,
        context=context,
    )

    sources = [
        {
            "document_id": doc["id"],
            "title": doc["title"],
            "category": doc["category"],
        }
        for doc in documents
    ]

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
    }