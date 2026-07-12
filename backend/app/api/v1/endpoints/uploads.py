from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.schemas.document import DocumentResponse
from app.services.document_ingestion_service import (
    DocumentIngestionError,
    ingest_document,
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
    Upload a TXT or Markdown file and store its content
    as a knowledge-base document.
    """
    parsed_tags = []

    if tags:
        parsed_tags = [
            tag.strip()
            for tag in tags.split(",")
            if tag.strip()
        ]

    try:
        document = await ingest_document(
            file=file,
            category=category,
            title=title,
            tags=parsed_tags,
            author=author,
        )

        return DocumentResponse(**document)

    except DocumentIngestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc