from typing import Any

from app.repositories import document_repository
from app.schemas.document import DocumentCreate, DocumentUpdate


async def create_document(document_data: DocumentCreate) -> dict[str, Any]:
    return await document_repository.create_document(document_data)


async def get_documents(
    category: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
    sort: str = "-created_at",
) -> list[dict[str, Any]]:
    return await document_repository.get_documents(
        category=category,
        search=search,
        page=page,
        limit=limit,
        sort=sort,
    )


async def get_document_by_id(document_id: str) -> dict[str, Any] | None:
    return await document_repository.get_document_by_id(document_id)


async def update_document(
    document_id: str,
    document_data: DocumentUpdate,
) -> dict[str, Any] | None:
    return await document_repository.update_document(document_id, document_data)


async def delete_document(document_id: str) -> bool:
    return await document_repository.delete_document(document_id)