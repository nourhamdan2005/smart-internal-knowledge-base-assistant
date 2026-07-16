import math
import logging
import re
from typing import Any

from app.ai.embedding_client import generate_embedding
from app.core.config import settings
from app.repositories.document_chunk_repository import (
    get_active_chunks_by_ids,
    get_active_chunks_with_embeddings,
    search_chunk_candidates,
)
from app.vectorstores.base import (
    VectorStoreError,
    VectorStoreUnavailableError,
)
from app.vectorstores.factory import get_vector_store


logger = logging.getLogger(__name__)


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
def calculate_character_overlap_ratio(
    first_chunk: dict[str, Any],
    second_chunk: dict[str, Any],
) -> float:
    """
    Calculate how much two chunks overlap using character positions.

    The ratio is measured against the smaller chunk so that a chunk
    contained almost entirely inside another is considered redundant.
    """
    if (
        first_chunk.get("document_id")
        != second_chunk.get("document_id")
    ):
        return 0.0

    first_start = first_chunk.get("start_character")
    first_end = first_chunk.get("end_character")
    second_start = second_chunk.get("start_character")
    second_end = second_chunk.get("end_character")

    if not all(
        isinstance(value, int)
        for value in [
            first_start,
            first_end,
            second_start,
            second_end,
        ]
    ):
        return 0.0

    first_length = max(first_end - first_start, 0)
    second_length = max(second_end - second_start, 0)

    smaller_length = min(
        first_length,
        second_length,
    )

    if smaller_length == 0:
        return 0.0

    overlap_start = max(
        first_start,
        second_start,
    )
    overlap_end = min(
        first_end,
        second_end,
    )

    overlap_length = max(
        overlap_end - overlap_start,
        0,
    )

    return overlap_length / smaller_length


def normalize_chunk_tokens(
    content: str,
) -> set[str]:
    """
    Convert chunk content into normalized tokens for similarity checks.
    """
    ignored_tokens = STOP_WORDS | {
        "all",
        "every",
    }

    raw_tokens = re.findall(
        r"[a-zA-Z0-9]+",
        content.lower(),
    )

    normalized_tokens: set[str] = set()

    for token in raw_tokens:
        if token in ignored_tokens:
            continue

        if token.endswith("ies") and len(token) > 4:
            token = f"{token[:-3]}y"
        elif token.endswith("s") and len(token) > 3:
            token = token[:-1]

        normalized_tokens.add(token)

    return normalized_tokens


def calculate_content_similarity(
    first_content: str,
    second_content: str,
) -> float:
    """
    Calculate Jaccard similarity between two chunks.
    """
    first_tokens = normalize_chunk_tokens(
        first_content
    )
    second_tokens = normalize_chunk_tokens(
        second_content
    )

    if not first_tokens or not second_tokens:
        return 0.0

    shared_tokens = (
        first_tokens
        & second_tokens
    )

    combined_tokens = (
        first_tokens
        | second_tokens
    )

    return len(shared_tokens) / len(combined_tokens)


def chunks_are_redundant(
    candidate: dict[str, Any],
    selected_chunk: dict[str, Any],
) -> bool:
    """
    Determine whether two chunks provide substantially duplicate context.
    """
    if (
        candidate.get("document_id")
        != selected_chunk.get("document_id")
    ):
        return False

    overlap_ratio = calculate_character_overlap_ratio(
        candidate,
        selected_chunk,
    )

    if (
        overlap_ratio
        >= settings.retrieval_overlap_threshold
    ):
        return True

    content_similarity = calculate_content_similarity(
        str(candidate.get("content", "")),
        str(selected_chunk.get("content", "")),
    )

    return (
        content_similarity
        >= settings.retrieval_similarity_threshold
    )


def select_diverse_chunks(
    scored_chunks: list[
        tuple[int, dict[str, Any]]
    ],
    limit: int,
) -> list[dict[str, Any]]:
    """
    Select high-scoring chunks while limiting repetition.

    Rules:
    - Respect the requested total limit.
    - Limit how many chunks can come from one document.
    - Skip strongly overlapping or near-duplicate chunks.
    """
    selected_chunks: list[dict[str, Any]] = []
    document_counts: dict[str, int] = {}

    for _, candidate in scored_chunks:
        document_id = str(
            candidate.get("document_id", "")
        )

        current_document_count = (
            document_counts.get(document_id, 0)
        )

        if (
            current_document_count
            >= settings.retrieval_max_chunks_per_document
        ):
            continue

        redundant = any(
            chunks_are_redundant(
                candidate,
                selected_chunk,
            )
            for selected_chunk in selected_chunks
        )

        if redundant:
            continue

        selected_chunks.append(candidate)

        document_counts[document_id] = (
            current_document_count + 1
        )

        if len(selected_chunks) >= limit:
            break

    return selected_chunks

def calculate_cosine_similarity(
    first_vector: list[float],
    second_vector: list[float],
) -> float:
    """
    Calculate cosine similarity between two embedding vectors.

    Returns 0 when either vector is empty, dimensions differ,
    or one vector has zero magnitude.
    """
    if not first_vector or not second_vector:
        return 0.0

    if len(first_vector) != len(second_vector):
        return 0.0

    dot_product = sum(
        first_value * second_value
        for first_value, second_value in zip(
            first_vector,
            second_vector,
        )
    )

    first_magnitude = math.sqrt(
        sum(value * value for value in first_vector)
    )

    second_magnitude = math.sqrt(
        sum(value * value for value in second_vector)
    )

    if first_magnitude == 0 or second_magnitude == 0:
        return 0.0

    similarity = dot_product / (
        first_magnitude * second_magnitude
    )

    return max(
        -1.0,
        min(1.0, similarity),
    )


def normalize_keyword_score(
    keyword_score: int,
) -> float:
    """
    Convert the open-ended keyword score into a 0–1 value.
    """
    if keyword_score <= 0:
        return 0.0

    return min(
        keyword_score / 100,
        1.0,
    )


def calculate_hybrid_score(
    keyword_score: int,
    semantic_similarity: float,
) -> float:
    """
    Combine normalized keyword relevance and semantic similarity.
    """
    normalized_keyword_score = normalize_keyword_score(
        keyword_score
    )

    normalized_semantic_score = max(
        0.0,
        semantic_similarity,
    )

    total_weight = (
        settings.hybrid_keyword_weight
        + settings.hybrid_semantic_weight
    )

    if total_weight <= 0:
        return 0.0

    weighted_score = (
        normalized_keyword_score
        * settings.hybrid_keyword_weight
        + normalized_semantic_score
        * settings.hybrid_semantic_weight
    )

    return weighted_score / total_weight


def merge_chunk_candidates(
    keyword_candidates: list[dict[str, Any]],
    semantic_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Merge candidate lists without returning the same chunk twice.
    """
    merged_candidates: dict[
        str,
        dict[str, Any],
    ] = {}

    for chunk in [
        *keyword_candidates,
        *semantic_candidates,
    ]:
        chunk_id = str(chunk.get("id", ""))

        if not chunk_id:
            continue

        existing_chunk = merged_candidates.get(
            chunk_id
        )

        if existing_chunk is None:
            merged_candidates[chunk_id] = chunk
            continue

        merged_chunk = {
            **existing_chunk,
            **chunk,
        }

        merged_candidates[chunk_id] = merged_chunk

    return list(merged_candidates.values())


async def hybrid_search_chunks(
    question: str,
    category: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Combine keyword and semantic retrieval into one ranked result.

    Keyword search remains available as a fallback when the
    embedding service cannot generate a query vector.
    """
    cleaned_question = question.strip()

    if not cleaned_question:
        return []

    result_limit = (
        limit
        if limit is not None
        else settings.retrieval_top_k
    )

    try:
        question_embedding = await generate_embedding(
            cleaned_question
        )
    except Exception:
        return await search_chunks(
            question=cleaned_question,
            category=category,
            limit=result_limit,
        )

    keywords = extract_keywords(cleaned_question)

    if not keywords:
        keywords = re.findall(
            r"[a-zA-Z0-9]+",
            cleaned_question.lower(),
        )

    keyword_candidates = await search_chunk_candidates(
        keywords=keywords,
        category=category,
        limit=settings.retrieval_candidate_limit,
    )

    semantic_candidates: list[dict[str, Any]] = []

    if settings.qdrant_enabled:
        try:
            store = get_vector_store()

            if store is None:
                raise VectorStoreUnavailableError(
                    "The configured vector store is unavailable."
                )

            vector_results = await store.search(
                embedding=question_embedding,
                category=category,
                limit=settings.qdrant_semantic_limit,
            )
            scores_by_chunk_id: dict[str, float] = {}

            for result in vector_results:
                existing_score = scores_by_chunk_id.get(
                    result.chunk_id
                )

                if (
                    existing_score is None
                    or result.score > existing_score
                ):
                    scores_by_chunk_id[result.chunk_id] = (
                        result.score
                    )

            hydrated_chunks = await get_active_chunks_by_ids(
                list(scores_by_chunk_id),
                category=category,
            )

            semantic_candidates = [
                {
                    **chunk,
                    "semantic_similarity": (
                        scores_by_chunk_id[chunk["id"]]
                    ),
                }
                for chunk in hydrated_chunks
                if chunk["id"] in scores_by_chunk_id
            ]
        except (VectorStoreError, TimeoutError, ConnectionError) as exc:
            if not settings.qdrant_fallback_enabled:
                if isinstance(exc, VectorStoreError):
                    raise

                raise VectorStoreUnavailableError(
                    "Semantic vector search is unavailable."
                ) from exc

            logger.warning(
                "Qdrant semantic retrieval failed; using local "
                "semantic fallback",
                exc_info=True,
            )

            semantic_candidates = []

            stored_chunks = await get_active_chunks_with_embeddings(
                category=category,
                limit=settings.semantic_candidate_limit,
            )

            for chunk in stored_chunks:
                chunk_embedding = chunk.get("embedding")
                similarity = (
                    calculate_cosine_similarity(
                        question_embedding,
                        chunk_embedding,
                    )
                    if isinstance(chunk_embedding, list)
                    else 0.0
                )
                semantic_candidates.append(
                    {
                        **chunk,
                        "semantic_similarity": similarity,
                    }
                )
    else:
        stored_chunks = await get_active_chunks_with_embeddings(
            category=category,
            limit=settings.semantic_candidate_limit,
        )

        for chunk in stored_chunks:
            chunk_embedding = chunk.get("embedding")
            similarity = (
                calculate_cosine_similarity(
                    question_embedding,
                    chunk_embedding,
                )
                if isinstance(chunk_embedding, list)
                else 0.0
            )
            semantic_candidates.append(
                {
                    **chunk,
                    "semantic_similarity": similarity,
                }
            )

    candidates = merge_chunk_candidates(
        keyword_candidates=keyword_candidates,
        semantic_candidates=semantic_candidates,
    )

    scored_chunks: list[
        tuple[float, dict[str, Any]]
    ] = []

    for chunk in candidates:
        keyword_score = calculate_chunk_relevance_score(
            chunk=chunk,
            keywords=keywords,
            original_question=cleaned_question,
        )

        semantic_similarity = float(
            chunk.get("semantic_similarity", 0.0)
        )

        if (
            keyword_score < settings.retrieval_min_score
            and semantic_similarity
            < settings.semantic_min_similarity
        ):
            continue

        hybrid_score = calculate_hybrid_score(
            keyword_score=keyword_score,
            semantic_similarity=semantic_similarity,
        )

        scored_chunk = {
            **chunk,
            "keyword_score": keyword_score,
            "semantic_similarity": semantic_similarity,
            "hybrid_score": hybrid_score,
        }

        scored_chunks.append(
            (
                hybrid_score,
                scored_chunk,
            )
        )

    scored_chunks.sort(
        key=lambda item: (
            item[0],
            item[1]["semantic_similarity"],
            item[1]["keyword_score"],
            -int(item[1].get("chunk_index", 0)),
        ),
        reverse=True,
    )

    return select_diverse_chunks(
        scored_chunks=scored_chunks,
        limit=result_limit,
    )


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

    return select_diverse_chunks(
        scored_chunks=scored_chunks,
        limit=result_limit,
    )
