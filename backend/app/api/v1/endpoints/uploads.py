
from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.repositories.document_repository import create_document
from app.schemas.document import DocumentResponse
from app.services.document_ingestion_service import (
    DocumentIngestionError,
    process_uploaded_document,
)


router = APIRouter()


@router.post(
    "/",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(...),
    title: str | None = Form(default=None),
    tags: str | None = Form(default=None),
    author: str = Form(default="Admin"),
) -> DocumentResponse:
    """
    Upload a TXT, Markdown, PDF, or DOCX file and store its
    extracted content as a knowledge-base document.
    """
    try:
        document_data = await process_uploaded_document(
            file=file,
            category=category,
            title=title,
            tags=tags,
            author=author,
        )

        document = await create_document(document_data)

        return DocumentResponse(**document)

    except DocumentIngestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
