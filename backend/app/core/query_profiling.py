from __future__ import annotations

import json
import logging
from contextvars import ContextVar, Token
from dataclasses import asdict, dataclass
from time import perf_counter
from types import TracebackType
from typing import Any

from app.core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class QueryTiming:
    preprocessing_ms: float | None = None
    embedding_ms: float | None = None
    keyword_search_ms: float | None = None
    vector_search_ms: float | None = None
    mongodb_validation_ms: float | None = None
    hybrid_ranking_ms: float | None = None
    redundancy_filtering_ms: float | None = None
    prompt_build_ms: float | None = None
    llm_generation_ms: float | None = None
    response_build_ms: float | None = None
    total_ms: float | None = None
    retrieved_keyword_candidates: int | None = None
    retrieved_vector_candidates: int | None = None
    validated_chunks: int | None = None
    final_context_chunks: int | None = None
    prompt_character_count: int | None = None
    answer_character_count: int | None = None
    fallback_path: str | None = None
    qdrant_used: bool = False
    embeddings_used: bool = False
    fallback_attempted: bool = False
    embedding_failed: bool = False
    qdrant_failed: bool = False
    ollama_failed: bool = False
    failed_stage: str | None = None
    exception_category: str | None = None
    ai_model: str | None = None
    embedding_model: str | None = None
    ollama_total_ms: float | None = None
    ollama_load_ms: float | None = None
    ollama_prompt_eval_ms: float | None = None
    ollama_eval_ms: float | None = None
    ollama_prompt_eval_count: int | None = None
    ollama_eval_count: int | None = None
    retrieval_complete_ms: float | None = None
    first_token_ms: float | None = None
    generation_stream_ms: float | None = None
    total_stream_ms: float | None = None
    output_token_count: int | None = None
    tokens_per_second: float | None = None
    client_disconnected: bool = False
    stream_completed: bool = False


class StageTimer:
    def __init__(self, profile: QueryProfiler, field: str) -> None:
        self.profile = profile
        self.field = field
        self.started_at = 0.0

    def __enter__(self) -> StageTimer:
        self.started_at = perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        elapsed = (perf_counter() - self.started_at) * 1000
        current = getattr(self.profile.timing, self.field)
        setattr(
            self.profile.timing,
            self.field,
            round((current or 0.0) + elapsed, 3),
        )
        if exc is not None:
            self.profile.mark_failure(self.field.removesuffix("_ms"), exc)

    async def __aenter__(self) -> StageTimer:
        return self.__enter__()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.__exit__(exc_type, exc, traceback)


class QueryProfiler:
    def __init__(self, enabled: bool | None = None) -> None:
        self.enabled = (
            settings.query_profiling_enabled if enabled is None else enabled
        )
        self.timing = QueryTiming(
            ai_model=settings.ollama_model,
            embedding_model=settings.embedding_model,
        )
        self.started_at = perf_counter()

    def stage(self, field: str) -> StageTimer:
        return StageTimer(self, field)

    def set(self, **values: Any) -> None:
        if not self.enabled:
            return
        for field, value in values.items():
            if hasattr(self.timing, field):
                setattr(self.timing, field, value)

    def mark_failure(self, stage: str, exc: BaseException) -> None:
        if self.enabled and self.timing.failed_stage is None:
            self.timing.failed_stage = stage
            self.timing.exception_category = type(exc).__name__

    def finish(self) -> None:
        if self.enabled:
            self.timing.total_ms = round(
                (perf_counter() - self.started_at) * 1000,
                3,
            )

    def payload(self) -> dict[str, Any]:
        values = asdict(self.timing)
        if not settings.query_profiling_include_counts:
            for field in (
                "retrieved_keyword_candidates",
                "retrieved_vector_candidates",
                "validated_chunks",
                "final_context_chunks",
                "prompt_character_count",
                "answer_character_count",
                "ollama_prompt_eval_count",
                "ollama_eval_count",
                "output_token_count",
            ):
                values.pop(field, None)
        values["event"] = "query_performance"
        values["slow"] = bool(
            self.timing.total_ms is not None
            and self.timing.total_ms >= settings.query_profiling_slow_threshold_ms
        )
        return {key: value for key, value in values.items() if value is not None}

    def log(self) -> None:
        if not self.enabled:
            return
        payload = self.payload()
        level = (
            logging.WARNING
            if payload["slow"]
            else getattr(logging, settings.query_profiling_log_level.upper())
        )
        logger.log(level, json.dumps(payload, separators=(",", ":")))

    def server_timing(self) -> str:
        names = {
            "embedding_ms": "embedding",
            "keyword_search_ms": "keyword",
            "vector_search_ms": "vector",
            "mongodb_validation_ms": "mongodb",
            "hybrid_ranking_ms": "ranking",
            "redundancy_filtering_ms": "diversity",
            "prompt_build_ms": "prompt",
            "llm_generation_ms": "llm",
            "response_build_ms": "response",
            "total_ms": "total",
            "first_token_ms": "first-token",
            "generation_stream_ms": "stream",
            "total_stream_ms": "total-stream",
        }
        return ", ".join(
            f"{label};dur={value:.1f}"
            for field, label in names.items()
            if (value := getattr(self.timing, field)) is not None
        )


_active_profiler: ContextVar[QueryProfiler | None] = ContextVar(
    "active_query_profiler",
    default=None,
)


def get_query_profiler() -> QueryProfiler | None:
    profiler = _active_profiler.get()
    return profiler if profiler is not None and profiler.enabled else None


def activate_query_profiler(profiler: QueryProfiler) -> Token[QueryProfiler | None]:
    return _active_profiler.set(profiler)


def deactivate_query_profiler(token: Token[QueryProfiler | None]) -> None:
    _active_profiler.reset(token)
