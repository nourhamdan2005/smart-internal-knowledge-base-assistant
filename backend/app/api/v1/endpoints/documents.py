from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.document import DocumentCreate, DocumentResponse, DocumentUpdate
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(document: DocumentCreate):
    return await document_service.create_document(document)


@router.get("", response_model=list[DocumentResponse])
async def get_documents(
    category: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    sort: str = Query(default="-created_at"),
):
    return await document_service.get_documents(
        category=category,
        search=search,
        page=page,
        limit=limit,
        sort=sort,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_by_id(document_id: str):
    document = await document_service.get_document_by_id(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(document_id: str, document: DocumentUpdate):
    updated_document = await document_service.update_document(document_id, document)

    if not updated_document:
        raise HTTPException(status_code=404, detail="Document not found")

    return updated_document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str):
    deleted = await document_service.delete_document(document_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    return None