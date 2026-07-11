import re
from typing import Any

from app.repositories.document_repository import get_documents


STOP_WORDS = {
    "what", "is", "the", "a", "an", "of", "to", "in", "on", "for",
    "and", "or", "how", "do", "does", "can", "i", "we", "you"
}


def extract_keywords(question: str) -> str:
    words = re.findall(r"\w+", question.lower())
    keywords = [word for word in words if word not in STOP_WORDS and len(word) > 2]

    if not keywords:
        return question

    return "|".join(keywords)


async def search_documents(
    question: str,
    category: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    search_query = extract_keywords(question)

    return await get_documents(
        category=category,
        search=search_query,
        page=1,
        limit=limit,
        sort="-created_at",
    )