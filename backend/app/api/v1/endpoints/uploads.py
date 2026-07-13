
from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.repositories.document_repository import (
    create_document,
    find_document_by_checksum,
)
from app.schemas.document import DocumentResponse
from app.services.document_chunk_service import (
    create_chunks_for_document,
)
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
    Upload a TXT, Markdown, PDF, or DOCX document.

    The file is validated, checked for duplicates, stored in MongoDB,
    and split into smaller searchable chunks.
    """
    try:
        document_data = await process_uploaded_document(
            file=file,
            category=category,
            title=title,
            tags=tags,
            author=author,
        )

        if not document_data.checksum:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="The uploaded file checksum could not be generated.",
            )

        duplicate_document = await find_document_by_checksum(
            document_data.checksum,
        )

        if duplicate_document is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This file has already been uploaded as "
                    f"'{duplicate_document['title']}'."
                ),
            )

        created_document = await create_document(
            document_data
        )

        await create_chunks_for_document(
            created_document,
        )

        return DocumentResponse(**created_document)

    except DocumentIngestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

