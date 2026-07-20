from typing import Any

from app.ai.embedding_client import generate_embedding
from app.core.config import settings
from app.repositories.document_chunk_repository import (
    create_document_chunks,
)
from app.schemas.document_chunk import DocumentChunkCreate
from app.services.document_chunking_service import (
    chunk_document_text,
)


async def create_chunks_for_document(
    document: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Generate chunks, create embeddings, and store them.
    """
    raw_chunks = chunk_document_text(
        text=document["content"],
    )

    chunk_models: list[DocumentChunkCreate] = []

    for chunk in raw_chunks:
        chunk_content = str(chunk["content"])

        embedding = await generate_embedding(
            chunk_content
        )

        chunk_models.append(
            DocumentChunkCreate(
                document_id=document["id"],
                chunk_index=int(
                    chunk["chunk_index"]
                ),
                content=chunk_content,
                start_character=int(
                    chunk["start_character"]
                ),
                end_character=int(
                    chunk["end_character"]
                ),
                character_count=int(
                    chunk["character_count"]
                ),
                category=document["category"],
                document_title=document["title"],
                embedding=embedding,
                embedding_model=(
                    settings.embedding_model
                ),
                embedding_dimensions=len(
                    embedding
                ),
                is_active=True,
            )
        )

    return await create_document_chunks(
        chunk_models
    )