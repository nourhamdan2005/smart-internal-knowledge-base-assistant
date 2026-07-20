import logging
from collections.abc import AsyncIterator
from time import perf_counter

import httpx
from ollama import AsyncClient, ResponseError

from app.core.config import settings
from app.core.query_profiling import get_query_profiler


logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Raised when the configured AI service cannot generate an answer."""


client = AsyncClient(
    host=settings.ollama_base_url,
    timeout=settings.ollama_request_timeout_seconds,
)


def answer_token_budget(question: str) -> int:
    """Choose a conservative output budget from explicit user intent."""
    normalized = question.lower()
    detailed_markers = ("detailed", "in depth", "comprehensive", "explain fully")
    moderate_markers = ("summarize", "summary", "steps", "procedure", "list", "compare", "explain")
    if any(marker in normalized for marker in detailed_markers):
        return min(320, settings.ollama_generation_num_predict * 2)
    if any(marker in normalized for marker in moderate_markers):
        return settings.ollama_generation_num_predict
    return min(96, settings.ollama_generation_num_predict)


def _messages(question: str, context: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a company internal knowledge assistant. Answer only using "
                "the supplied company documents. Do not add unsupported information. "
                "If the answer is absent, say exactly: \"I couldn't find this information "
                "in the available documents.\" Be concise and direct by default. Give "
                "complete steps or detail only when requested. Do not repeat the question, "
                "evidence, introductions, or conclusions."
            ),
        },
        {"role": "user", "content": f"Company documents:\n\n{context}\n\nQuestion:\n{question}"},
    ]


def _options(question: str) -> dict[str, float | int]:
    return {
        "temperature": settings.ollama_generation_temperature,
        "top_p": settings.ollama_generation_top_p,
        "top_k": settings.ollama_generation_top_k,
        "repeat_penalty": settings.ollama_generation_repeat_penalty,
        "num_ctx": settings.ollama_generation_num_ctx,
        "num_predict": answer_token_budget(question),
    }


def _record_ollama_metadata(response: dict) -> None:
    profiler = get_query_profiler()
    if not profiler:
        return
    nanoseconds = {
        "ollama_total_ms": "total_duration",
        "ollama_load_ms": "load_duration",
        "ollama_prompt_eval_ms": "prompt_eval_duration",
        "ollama_eval_ms": "eval_duration",
    }
    values = {
        field: round(float(response[key]) / 1_000_000, 3)
        for field, key in nanoseconds.items()
        if response.get(key) is not None
    }
    eval_count = response.get("eval_count")
    eval_duration = response.get("eval_duration")
    if eval_count and eval_duration:
        values["tokens_per_second"] = round(
            float(eval_count) / (float(eval_duration) / 1_000_000_000), 3
        )
    profiler.set(
        **values,
        ollama_prompt_eval_count=response.get("prompt_eval_count"),
        ollama_eval_count=eval_count,
        output_token_count=eval_count,
    )


async def stream_answer(question: str, context: str) -> AsyncIterator[str]:
    """Yield validated Ollama text deltas and retain final metadata."""
    profiler = get_query_profiler()
    started = perf_counter()
    first_token_seen = False
    try:
        stream = await client.chat(
            model=settings.ollama_model,
            messages=_messages(question, context),
            options=_options(question),
            keep_alive=settings.ollama_keep_alive,
            stream=True,
        )
        async for part in stream:
            text = part.get("message", {}).get("content", "")
            if text:
                if profiler and not first_token_seen:
                    profiler.set(first_token_ms=round((perf_counter() - started) * 1000, 3))
                first_token_seen = True
                yield text
            if part.get("done"):
                _record_ollama_metadata(part)
        if not first_token_seen:
            raise AIServiceError("The AI service returned an empty response.")
    except httpx.TimeoutException as exc:
        raise AIServiceError("The AI service took too long to respond.") from exc
    except httpx.ConnectError as exc:
        raise AIServiceError("The AI service is currently unavailable.") from exc
    except ResponseError as exc:
        raise AIServiceError("The AI service could not generate an answer.") from exc
    except httpx.RequestError as exc:
        raise AIServiceError("The AI service is currently unavailable.") from exc
    finally:
        if profiler:
            profiler.set(generation_stream_ms=round((perf_counter() - started) * 1000, 3))


async def generate_answer(question: str, context: str) -> str:
    try:
        response = await client.chat(
            model=settings.ollama_model,
            messages=_messages(question, context),
            options=_options(question),
            keep_alive=settings.ollama_keep_alive,
        )

        answer = response.get("message", {}).get("content", "").strip()

        _record_ollama_metadata(response)

        if not answer:
            logger.error("Ollama returned a response without answer content.")
            raise AIServiceError(
                "The AI service returned an empty response."
            )

        return answer

    except httpx.TimeoutException as exc:
        logger.exception("Ollama request timed out.")
        raise AIServiceError(
            "The AI service took too long to respond."
        ) from exc

    except httpx.ConnectError as exc:
        logger.exception("Could not connect to Ollama.")
        raise AIServiceError(
            "The AI service is currently unavailable."
        ) from exc

    except ResponseError as exc:
        logger.exception(
            "Ollama returned an error. Status: %s",
            exc.status_code,
        )

        if exc.status_code == 404:
            raise AIServiceError(
                f"The configured AI model "
                f"'{settings.ollama_model}' is not available."
            ) from exc

        raise AIServiceError(
            "The AI service could not generate an answer."
        ) from exc

    except httpx.RequestError as exc:
        logger.exception("An HTTP error occurred while calling Ollama.")
        raise AIServiceError(
            "The AI service is currently unavailable."
        ) from exc

    except AIServiceError:
        raise

    except Exception as exc:
        profiler = get_query_profiler()
        if profiler:
            profiler.set(ollama_failed=True)
        logger.exception("Unexpected Ollama client error.")
        raise AIServiceError(
            "An unexpected AI service error occurred."
        ) from exc
