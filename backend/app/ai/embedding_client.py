from google import genai
from google.genai import types
from ollama import AsyncClient, ResponseError

from app.core.config import settings


ollama_client = AsyncClient(
    host=settings.ollama_base_url,
)

gemini_client = (
    genai.Client(api_key=settings.gemini_api_key)
    if settings.gemini_api_key
    else None
)


async def _generate_ollama_embedding(
    text: str,
) -> list[float]:
    try:
        response = await ollama_client.embeddings(
            model=settings.embedding_model,
            prompt=text,
        )
    except ResponseError as exc:
        raise RuntimeError(
            "Embedding generation failed."
        ) from exc

    embedding = response.get("embedding")

    if not embedding:
        raise RuntimeError(
            "Embedding model returned no vector."
        )

    return [float(value) for value in embedding]


async def _generate_gemini_embedding(
    text: str,
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[float]:
    if gemini_client is None:
        raise RuntimeError(
            "Gemini is selected but GEMINI_API_KEY "
            "is not configured."
        )

    try:
        response = await gemini_client.aio.models.embed_content(
            model=settings.gemini_embedding_model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=(
                    settings.gemini_embedding_dimensions
                ),
            ),
        )
    except Exception as exc:
        raise RuntimeError(
            "Gemini embedding generation failed."
        ) from exc

    if not response.embeddings:
        raise RuntimeError(
            "Gemini returned no embedding."
        )

    values = response.embeddings[0].values

    if not values:
        raise RuntimeError(
            "Gemini returned an empty embedding."
        )

    return [float(value) for value in values]


async def generate_embedding(
    text: str,
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[float]:
    cleaned_text = text.strip()

    if not cleaned_text:
        raise ValueError(
            "Embedding text cannot be empty."
        )

    provider = settings.embedding_provider.strip().lower()

    if provider == "ollama":
        return await _generate_ollama_embedding(
            cleaned_text
        )

    if provider == "gemini":
        return await _generate_gemini_embedding(
            cleaned_text,
            task_type=task_type,
        )

    raise RuntimeError(
        f"Unsupported embedding provider: "
        f"{settings.embedding_provider}"
    )
