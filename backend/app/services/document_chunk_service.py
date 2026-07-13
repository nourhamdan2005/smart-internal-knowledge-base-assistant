from typing import Any

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
    Generate and store chunks for one document.
    """
    raw_chunks = chunk_document_text(
        text=document["content"],
    )

    chunk_models = [
        DocumentChunkCreate(
            document_id=document["id"],
            chunk_index=int(chunk["chunk_index"]),
            content=str(chunk["content"]),
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
            is_active=True,
        )
        for chunk in raw_chunks
    ]

    return await create_document_chunks(chunk_models)