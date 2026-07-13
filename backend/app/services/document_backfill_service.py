from typing import Any

from app.repositories.document_chunk_repository import (
    get_document_ids_with_active_chunks,
)
from app.repositories.document_repository import (
    get_all_active_documents,
)
from app.services.document_chunk_service import (
    create_chunks_for_document,
)
from app.services.document_chunking_service import (
    DocumentChunkingError,
)


async def backfill_missing_document_chunks() -> dict[str, Any]:
    """
    Generate chunks for active documents that have none.

    Documents with active chunks are skipped, making the
    operation safe to run more than once.
    """
    documents = await get_all_active_documents()

    chunked_document_ids = (
        await get_document_ids_with_active_chunks()
    )

    result: dict[str, Any] = {
        "total_documents": len(documents),
        "processed_documents": 0,
        "skipped_documents": 0,
        "failed_documents": 0,
        "created_chunks": 0,
        "failures": [],
    }

    for document in documents:
        document_id = document["id"]

        if document_id in chunked_document_ids:
            result["skipped_documents"] += 1
            continue

        try:
            created_chunks = await create_chunks_for_document(
                document,
            )

            result["processed_documents"] += 1
            result["created_chunks"] += len(
                created_chunks
            )

            chunked_document_ids.add(document_id)

        except DocumentChunkingError as exc:
            result["failed_documents"] += 1

            result["failures"].append(
                {
                    "document_id": document_id,
                    "title": document["title"],
                    "error": str(exc),
                }
            )

    return result