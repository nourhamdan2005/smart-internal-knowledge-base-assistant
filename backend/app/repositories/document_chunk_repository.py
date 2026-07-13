import re
from datetime import datetime
from typing import Any

from app.core.database import database
from app.schemas.document_chunk import DocumentChunkCreate


collection = database["document_chunks"]


def chunk_helper(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(chunk["_id"]),
        "document_id": chunk["document_id"],
        "chunk_index": chunk["chunk_index"],
        "content": chunk["content"],
        "start_character": chunk["start_character"],
        "end_character": chunk["end_character"],
        "character_count": chunk["character_count"],
        "category": chunk["category"],
        "document_title": chunk["document_title"],
        "is_active": chunk.get("is_active", True),
        "created_at": chunk["created_at"],
        "updated_at": chunk["updated_at"],
    }


async def create_document_chunks(
    chunks: list[DocumentChunkCreate],
) -> list[dict[str, Any]]:
    if not chunks:
        return []

    now = datetime.utcnow()

    chunk_documents = []

    for chunk in chunks:
        chunk_document = chunk.model_dump()
        chunk_document["created_at"] = now
        chunk_document["updated_at"] = now
        chunk_documents.append(chunk_document)

    result = await collection.insert_many(chunk_documents)

    created_chunks = []

    cursor = collection.find(
        {
            "_id": {
                "$in": result.inserted_ids,
            }
        }
    ).sort("chunk_index", 1)

    async for chunk in cursor:
        created_chunks.append(chunk_helper(chunk))

    return created_chunks


async def get_chunks_by_document_id(
    document_id: str,
) -> list[dict[str, Any]]:
    cursor = collection.find(
        {
            "document_id": document_id,
            "is_active": True,
        }
    ).sort("chunk_index", 1)

    chunks = []

    async for chunk in cursor:
        chunks.append(chunk_helper(chunk))

    return chunks


async def deactivate_chunks_by_document_id(
    document_id: str,
) -> int:
    result = await collection.update_many(
        {
            "document_id": document_id,
            "is_active": True,
        },
        {
            "$set": {
                "is_active": False,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    return result.modified_count
async def search_chunk_candidates(
    keywords: list[str],
    category: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Retrieve active chunks containing at least one keyword
    in their document title or content.
    """
    if not keywords:
        return []

    query: dict[str, Any] = {
        "is_active": True,
    }

    if category:
        query["category"] = category

    search_conditions: list[dict[str, Any]] = []

    for keyword in keywords:
        safe_keyword = re.escape(keyword)

        search_conditions.extend(
            [
                {
                    "document_title": {
                        "$regex": safe_keyword,
                        "$options": "i",
                    }
                },
                {
                    "content": {
                        "$regex": safe_keyword,
                        "$options": "i",
                    }
                },
            ]
        )

    query["$or"] = search_conditions

    cursor = collection.find(query).limit(limit)

    chunks: list[dict[str, Any]] = []

    async for chunk in cursor:
        chunks.append(chunk_helper(chunk))

    return chunks