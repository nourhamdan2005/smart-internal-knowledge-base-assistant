from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies.auth import (
    require_admin,
    require_authenticated,
    require_editor_or_admin,
)
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentUpdate
from app.services import document_service

router = APIRouter(tags=["Documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document: DocumentCreate,
    _current_user=Depends(require_editor_or_admin),
):
    return await document_service.create_document(document)


@router.get("", response_model=list[DocumentResponse])
async def get_documents(
    category: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    sort: str = Query(default="-created_at"),
    _current_user=Depends(require_authenticated),
):
    return await document_service.get_documents(
        category=category,
        search=search,
        page=page,
        limit=limit,
        sort=sort,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_by_id(
    document_id: str,
    _current_user=Depends(require_authenticated),
):
    document = await document_service.get_document_by_id(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    document: DocumentUpdate,
    _current_user=Depends(require_editor_or_admin),
):
    updated_document = await document_service.update_document(document_id, document)

    if not updated_document:
        raise HTTPException(status_code=404, detail="Document not found")

    return updated_document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    _current_user=Depends(require_admin),
):
    deleted = await document_service.delete_document(document_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    return None
