import re
from typing import Any

from app.repositories.document_chunk_repository import (
    search_chunk_candidates,
)


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
    words = re.findall(
        r"[a-zA-Z0-9]+",
        question.lower(),
    )

    keywords = [
        word
        for word in words
        if word not in STOP_WORDS and len(word) > 2
    ]

    return list(dict.fromkeys(keywords))


def calculate_chunk_relevance_score(
    chunk: dict[str, Any],
    keywords: list[str],
    original_question: str,
) -> int:
    document_title = str(
        chunk.get("document_title", "")
    ).lower()

    content = str(
        chunk.get("content", "")
    ).lower()

    score = 0

    for keyword in keywords:
        if keyword in document_title:
            score += 10

        if keyword in content:
            score += 2

    normalized_question = " ".join(
        re.findall(
            r"[a-zA-Z0-9]+",
            original_question.lower(),
        )
    )

    if (
        normalized_question
        and normalized_question in document_title
    ):
        score += 20

    if normalized_question and normalized_question in content:
        score += 10

    searchable_text = " ".join(
        [
            document_title,
            content,
        ]
    )

    if keywords and all(
        keyword in searchable_text
        for keyword in keywords
    ):
        score += 15

    return score


async def search_chunks(
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

    candidates = await search_chunk_candidates(
        keywords=keywords,
        category=category,
        limit=50,
    )

    ranked_chunks = sorted(
        candidates,
        key=lambda chunk: calculate_chunk_relevance_score(
            chunk=chunk,
            keywords=keywords,
            original_question=cleaned_question,
        ),
        reverse=True,
    )

    return ranked_chunks[:limit]