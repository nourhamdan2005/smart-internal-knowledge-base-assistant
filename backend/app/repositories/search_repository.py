import re
from typing import Any

from app.core.config import settings
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
    """
    Extract meaningful, unique search keywords from a question.
    """
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


def count_word_occurrences(
    text: str,
    word: str,
) -> int:
    """
    Count whole-word occurrences without matching partial words.

    For example, searching for 'work' does not count 'worker'.
    """
    pattern = rf"\b{re.escape(word)}\b"

    return len(
        re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
    )


def calculate_chunk_relevance_score(
    chunk: dict[str, Any],
    keywords: list[str],
    original_question: str,
) -> int:
    """
    Calculate a keyword relevance score for one document chunk.

    Chunk content carries more weight than the document title
    because the content is what is provided to the language model.
    """
    document_title = str(
        chunk.get("document_title", "")
    ).lower()

    content = str(
        chunk.get("content", "")
    ).lower()

    if not keywords:
        return 0

    score = 0
    matched_keywords = 0

    for keyword in keywords:
        title_occurrences = count_word_occurrences(
            document_title,
            keyword,
        )
        content_occurrences = count_word_occurrences(
            content,
            keyword,
        )

        if title_occurrences > 0:
            score += min(title_occurrences, 2) * 3

        if content_occurrences > 0:
            score += min(content_occurrences, 5) * 5

        if (
            title_occurrences > 0
            or content_occurrences > 0
        ):
            matched_keywords += 1

    keyword_phrase = " ".join(keywords)

    if keyword_phrase:
        if keyword_phrase in document_title:
            score += 10

        if keyword_phrase in content:
            score += 20

    coverage_ratio = matched_keywords / len(keywords)

    score += round(coverage_ratio * 10)

    if matched_keywords == len(keywords):
        score += 15

    return score


async def search_chunks(
    question: str,
    category: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Search, score, filter, and rank document chunks.
    """
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

    result_limit = (
        limit
        if limit is not None
        else settings.retrieval_top_k
    )

    candidates = await search_chunk_candidates(
        keywords=keywords,
        category=category,
        limit=settings.retrieval_candidate_limit,
    )

    scored_chunks: list[
        tuple[int, dict[str, Any]]
    ] = []

    for chunk in candidates:
        score = calculate_chunk_relevance_score(
            chunk=chunk,
            keywords=keywords,
            original_question=cleaned_question,
        )

        if score < settings.retrieval_min_score:
            continue

        scored_chunks.append(
            (
                score,
                chunk,
            )
        )

    scored_chunks.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        chunk
        for _, chunk in scored_chunks[:result_limit]
    ]