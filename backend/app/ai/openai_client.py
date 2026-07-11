import logging

import httpx
from ollama import AsyncClient, ResponseError

from app.core.config import settings


logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Raised when the configured AI service cannot generate an answer."""


client = AsyncClient(
    host=settings.ollama_base_url,
    timeout=120.0,
)


async def generate_answer(question: str, context: str) -> str:
    try:
        response = await client.chat(
            model=settings.ollama_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a company internal knowledge assistant. "
                        "Answer only using the supplied company documents. "
                        "Do not add information that is not supported by "
                        "the documents. "
                        "If the answer is not present, say exactly: "
                        "\"I couldn't find this information in the "
                        "available documents.\""
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Company documents:\n\n"
                        f"{context}\n\n"
                        "Question:\n"
                        f"{question}"
                    ),
                },
            ],
            options={
                "temperature": 0.2,
            },
        )

        answer = response.get("message", {}).get("content", "").strip()

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
        logger.exception("Unexpected Ollama client error.")
        raise AIServiceError(
            "An unexpected AI service error occurred."
        ) from exc