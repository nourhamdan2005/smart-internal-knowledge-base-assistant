import json
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse

from app.ai.openai_client import AIServiceError
from app.schemas.query import QueryRequest, QueryResponse
from app.core.config import settings
from app.core.query_profiling import (
    QueryProfiler,
    activate_query_profiler,
    deactivate_query_profiler,
)
from app.services.query_service import prepare_query, query_documents
from app.ai.openai_client import stream_answer
from app.vectorstores.base import VectorStoreError
from app.dependencies.auth import require_authenticated

router = APIRouter(
    dependencies=[Depends(require_authenticated)],
)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/stream")
async def stream_knowledge_base(request_body: QueryRequest, request: Request):
    if not settings.query_streaming_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Streaming is disabled.")

    async def events():
        profiler = QueryProfiler()
        token = activate_query_profiler(profiler)
        started = perf_counter()
        answer_parts: list[str] = []
        try:
            yield _sse("status", {"stage": "started"})
            prepared = await prepare_query(request_body.question.strip(), request_body.category)
            profiler.set(retrieval_complete_ms=round((perf_counter() - started) * 1000, 3))
            yield _sse("status", {"stage": "retrieval_complete"})

            if not prepared["chunks"]:
                answer = prepared["fallback_response"]["answer"]
                answer_parts.append(answer)
                yield _sse("delta", {"text": answer})
                yield _sse("sources", {"sources": []})
            else:
                buffer = ""
                first_delta = True
                async for delta in stream_answer(request_body.question, prepared["context"]):
                    if await request.is_disconnected():
                        profiler.set(client_disconnected=True)
                        return
                    answer_parts.append(delta)
                    if first_delta:
                        profiler.set(first_token_ms=round((perf_counter() - started) * 1000, 3))
                        first_delta = False
                    buffer += delta
                    if not answer_parts[:-1] or len(buffer) >= 24 or buffer.endswith((". ", "\n")):
                        yield _sse("delta", {"text": buffer})
                        buffer = ""
                if buffer:
                    yield _sse("delta", {"text": buffer})
                yield _sse("sources", {"sources": prepared["sources"]})

            profiler.set(
                answer_character_count=len("".join(answer_parts)),
                stream_completed=True,
            )
            yield _sse("done", {
                "completed": True,
                "performance": {
                    "retrieval_ms": profiler.timing.retrieval_complete_ms,
                    "first_token_ms": profiler.timing.first_token_ms,
                    "generation_ms": profiler.timing.generation_stream_ms,
                    "output_tokens": profiler.timing.output_token_count,
                    "tokens_per_second": profiler.timing.tokens_per_second,
                    "context_chunks": profiler.timing.final_context_chunks,
                },
            })
        except Exception as exc:
            profiler.mark_failure("stream", exc)
            profiler.set(ollama_failed=isinstance(exc, AIServiceError))
            yield _sse("error", {"message": "The answer stream was interrupted. Please retry."})
        finally:
            profiler.set(total_stream_ms=round((perf_counter() - started) * 1000, 3))
            profiler.finish()
            profiler.log()
            deactivate_query_profiler(token)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post(
    "/",
    response_model=QueryResponse,
)
async def query_knowledge_base(
    request: QueryRequest,
    response: Response = Response(),
) -> QueryResponse:
    profiler = QueryProfiler()
    token = activate_query_profiler(profiler)
    try:
        with profiler.stage("preprocessing_ms"):
            question = request.question.strip()
            category = request.category.strip() if request.category else None

        result = await query_documents(question=question, category=category)

        with profiler.stage("response_build_ms"):
            query_response = QueryResponse(**result)

        return query_response

    except AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except VectorStoreError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Semantic search is temporarily unavailable.",
        ) from exc
    finally:
        profiler.finish()
        if settings.query_profiling_server_timing_enabled and profiler.enabled:
            response.headers["Server-Timing"] = profiler.server_timing()
        profiler.log()
        deactivate_query_profiler(token)
