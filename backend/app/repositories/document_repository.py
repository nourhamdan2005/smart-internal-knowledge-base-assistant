
import re
from datetime import datetime
from typing import Any

from bson import ObjectId

from app.core.database import database
from app.schemas.document import DocumentCreate, DocumentUpdate


collection = database["documents"]


def document_helper(document: dict[str, Any]) -> dict[str, Any]:
    """
    Convert a MongoDB document into an API-friendly dictionary.
    """
    return {
        "id": str(document["_id"]),
        "title": document["title"],
        "category": document["category"],
        "content": document["content"],
        "tags": document.get("tags", []),
        "author": document.get("author", "Admin"),
        "is_active": document.get("is_active", True),
        "created_at": document["created_at"],
        "updated_at": document["updated_at"],
        "original_filename": document.get("original_filename"),
        "extension": document.get("extension"),
        "mime_type": document.get("mime_type"),
        "file_size": document.get("file_size"),
        "checksum": document.get("checksum"),
        "uploaded_at": document.get("uploaded_at"),
    }


async def create_document(
    document_data: DocumentCreate,
) -> dict[str, Any]:
    """
    Create a new active knowledge-base document.
    """
    now = datetime.utcnow()

    document = document_data.model_dump()
    document["is_active"] = True
    document["created_at"] = now
    document["updated_at"] = now

    result = await collection.insert_one(document)

    created_document = await collection.find_one(
        {"_id": result.inserted_id}
    )

    return document_helper(created_document)


async def get_documents(
    category: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
    sort: str = "-created_at",
) -> list[dict[str, Any]]:
    """
    Return active documents with optional filtering, search,
    pagination, and sorting.
    """
    query: dict[str, Any] = {
        "is_active": True,
    }

    if category:
        query["category"] = category

    if search:
        safe_search = re.escape(search)

        query["$or"] = [
            {
                "title": {
                    "$regex": safe_search,
                    "$options": "i",
                }
            },
            {
                "content": {
                    "$regex": safe_search,
                    "$options": "i",
                }
            },
            {
                "tags": {
                    "$regex": safe_search,
                    "$options": "i",
                }
            },
        ]

    sort_field = sort.lstrip("-")
    sort_order = -1 if sort.startswith("-") else 1

    cursor = (
        collection.find(query)
        .sort(sort_field, sort_order)
        .skip((page - 1) * limit)
        .limit(limit)
    )

    documents: list[dict[str, Any]] = []

    async for document in cursor:
        documents.append(document_helper(document))

    return documents


async def search_document_candidates(
    keywords: list[str],
    category: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Retrieve active documents containing at least one keyword
    in their title, content, or tags.
    """
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
                    "title": {
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
                {
                    "tags": {
                        "$regex": safe_keyword,
                        "$options": "i",
                    }
                },
            ]
        )

    if search_conditions:
        query["$or"] = search_conditions

    cursor = collection.find(query).limit(limit)

    documents: list[dict[str, Any]] = []

    async for document in cursor:
        documents.append(document_helper(document))

    return documents


async def get_document_by_id(
    document_id: str,
) -> dict[str, Any] | None:
    """
    Return one active document by its MongoDB ObjectId.
    """
    if not ObjectId.is_valid(document_id):
        return None

    document = await collection.find_one(
        {
            "_id": ObjectId(document_id),
            "is_active": True,
        }
    )

    if document is None:
        return None

    return document_helper(document)


async def update_document(
    document_id: str,
    document_data: DocumentUpdate,
) -> dict[str, Any] | None:
    """
    Update an active document.
    """
    if not ObjectId.is_valid(document_id):
        return None

    update_data = document_data.model_dump(
        exclude_unset=True,
    )
    update_data["updated_at"] = datetime.utcnow()

    result = await collection.update_one(
        {
            "_id": ObjectId(document_id),
            "is_active": True,
        },
        {
            "$set": update_data,
        },
    )

    if result.matched_count == 0:
        return None

    updated_document = await collection.find_one(
        {
            "_id": ObjectId(document_id),
        }
    )

    if updated_document is None:
        return None

    return document_helper(updated_document)


async def delete_document(
    document_id: str,
) -> bool:
    """
    Soft-delete a document by setting is_active to False.
    """
    if not ObjectId.is_valid(document_id):
        return False

    result = await collection.update_one(
        {
            "_id": ObjectId(document_id),
            "is_active": True,
        },
        {
            "$set": {
                "is_active": False,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    return result.matched_count > 0


async def find_document_by_checksum(
    checksum: str,
) -> dict[str, Any] | None:
    """
    Find an active document with the same uploaded-file checksum.
    """
    document = await collection.find_one(
        {
            "checksum": checksum,
            "is_active": True,
        }
    )

    if document is None:
        return None

    return document_helper(document)

async def get_all_active_documents() -> list[dict[str, Any]]:
    """
    Return all active documents for maintenance operations.
    """
    cursor = collection.find(
        {
            "is_active": True,
        }
    )

    documents: list[dict[str, Any]] = []

    async for document in cursor:
        documents.append(document_helper(document))

    return documents