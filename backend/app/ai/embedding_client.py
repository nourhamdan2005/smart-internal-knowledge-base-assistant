from ollama import AsyncClient, ResponseError

from app.core.config import settings


client = AsyncClient(
    host=settings.ollama_base_url,
)


async def generate_embedding(
    text: str,
) -> list[float]:
    """
    Generate an embedding vector for the provided text using
    the local Ollama embedding model.
    """
    cleaned_text = text.strip()

    if not cleaned_text:
        raise ValueError(
            "Embedding text cannot be empty."
        )

    try:
        response = await client.embeddings(
            model=settings.embedding_model,
            prompt=cleaned_text,
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

    return embedding
