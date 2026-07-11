import re
from typing import Any

from app.repositories.document_repository import search_document_candidates


STOP_WORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "can",
    "could",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "please",
    "should",
    "tell",
    "the",
    "this",
    "to",
    "we",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "would",
    "you",
    "your",
}


def extract_keywords(question: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9]+", question.lower())

    keywords = [
        word
        for word in words
        if word not in STOP_WORDS and len(word) > 2
    ]

    return list(dict.fromkeys(keywords))


def calculate_relevance_score(
    document: dict[str, Any],
    keywords: list[str],
    original_question: str,
) -> int:
    title = str(document.get("title", "")).lower()
    content = str(document.get("content", "")).lower()

    tags = [
        str(tag).lower()
        for tag in document.get("tags", [])
    ]

    score = 0

    for keyword in keywords:
        if keyword in title:
            score += 10

        if any(keyword in tag for tag in tags):
            score += 6

        if keyword in content:
            score += 2

    normalized_question = " ".join(
        re.findall(
            r"[a-zA-Z0-9]+",
            original_question.lower(),
        )
    )

    if normalized_question and normalized_question in title:
        score += 20

    if normalized_question and normalized_question in content:
        score += 10

    searchable_text = " ".join([title, content, *tags])

    if keywords and all(
        keyword in searchable_text
        for keyword in keywords
    ):
        score += 15

    return score


async def search_documents(
    question: str,
    category: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    cleaned_question = question.strip()

    if not cleaned_question:
        return []

    keywords = extract_keywords(cleaned_question)

    if not keywords:
        keywords = re.findall(
            r"[a-zA-Z0-9]+",
            cleaned_question.lower(),
        )

    if not keywords:
        return []

    candidates = await search_document_candidates(
        keywords=keywords,
        category=category,
        limit=50,
    )

    ranked_documents = sorted(
        candidates,
        key=lambda document: calculate_relevance_score(
            document=document,
            keywords=keywords,
            original_question=cleaned_question,
        ),
        reverse=True,
    )

    return ranked_documents[:limit]
