from typing import Any

from pymongo import ASCENDING, DESCENDING, IndexModel

from app.core.database import database


DOCUMENT_INDEXES = [
    IndexModel(
        [
            ("is_active", ASCENDING),
        ],
        name="documents_is_active_idx",
    ),
    IndexModel(
        [
            ("category", ASCENDING),
            ("is_active", ASCENDING),
        ],
        name="documents_category_active_idx",
    ),
    IndexModel(
        [
            ("is_active", ASCENDING),
            ("created_at", DESCENDING),
        ],
        name="documents_active_created_at_idx",
    ),
    IndexModel(
        [
            ("checksum", ASCENDING),
            ("is_active", ASCENDING),
        ],
        name="documents_checksum_active_idx",
    ),
]


DOCUMENT_CHUNK_INDEXES = [
    IndexModel(
        [
            ("document_id", ASCENDING),
            ("is_active", ASCENDING),
        ],
        name="chunks_document_active_idx",
    ),
    IndexModel(
        [
            ("category", ASCENDING),
            ("is_active", ASCENDING),
        ],
        name="chunks_category_active_idx",
    ),
    IndexModel(
        [
            ("document_title", ASCENDING),
            ("is_active", ASCENDING),
        ],
        name="chunks_title_active_idx",
    ),
    IndexModel(
        [
            ("document_id", ASCENDING),
            ("chunk_index", ASCENDING),
        ],
        name="chunks_document_index_idx",
    ),
    IndexModel(
        [
            ("is_active", ASCENDING),
        ],
        name="chunks_is_active_idx",
    ),
]


USER_INDEXES = [
    IndexModel(
        [
            ("email", ASCENDING),
        ],
        name="users_email_unique_idx",
        unique=True,
    ),
    IndexModel(
        [
            ("role", ASCENDING),
            ("is_active", ASCENDING),
        ],
        name="users_role_active_idx",
    ),
]


async def create_database_indexes() -> dict[str, list[str]]:
    """
    Create all required MongoDB indexes.

    MongoDB index creation is idempotent. Existing indexes with
    matching definitions are reused.
    """
    documents_collection = database["documents"]
    chunks_collection = database["document_chunks"]
    users_collection = database["users"]

    document_index_names = (
        await documents_collection.create_indexes(
            DOCUMENT_INDEXES
        )
    )

    chunk_index_names = (
        await chunks_collection.create_indexes(
            DOCUMENT_CHUNK_INDEXES
        )
    )

    user_index_names = await users_collection.create_indexes(
        USER_INDEXES
    )

    return {
        "documents": document_index_names,
        "document_chunks": chunk_index_names,
        "users": user_index_names,
    }


async def get_database_index_information() -> dict[
    str,
    dict[str, Any],
]:
    """
    Return index metadata for supported collections.
    """
    documents_collection = database["documents"]
    chunks_collection = database["document_chunks"]
    users_collection = database["users"]

    return {
        "documents": (
            await documents_collection.index_information()
        ),
        "document_chunks": (
            await chunks_collection.index_information()
        ),
        "users": await users_collection.index_information(),
    }
async def explain_active_chunk_lookup(
    document_id: str,
) -> dict[str, Any]:
    """
    Return MongoDB's execution plan for an active chunk lookup.
    """
    collection = database["document_chunks"]

    cursor = collection.find(
        {
            "document_id": document_id,
            "is_active": True,
        }
    )

    return await cursor.explain()
