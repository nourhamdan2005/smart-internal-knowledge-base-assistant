from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.repositories.document_chunk_repository import (
    create_document_chunks,
)
from app.repositories.document_repository import (
    create_document,
    find_document_by_checksum,
)
from app.schemas.document import DocumentResponse
from app.schemas.document_chunk import DocumentChunkCreate
from app.services.document_chunking_service import (
    chunk_document_text,
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

    The uploaded file is validated, checked for duplicates,
    stored in MongoDB, and split into searchable chunks.
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

        created_document = await create_document(document_data)

        raw_chunks = chunk_document_text(
            text=created_document["content"],
        )

        chunk_models = [
            DocumentChunkCreate(
                document_id=created_document["id"],
                chunk_index=int(chunk["chunk_index"]),
                content=str(chunk["content"]),
                start_character=int(chunk["start_character"]),
                end_character=int(chunk["end_character"]),
                character_count=int(chunk["character_count"]),
                category=created_document["category"],
                document_title=created_document["title"],
                is_active=True,
            )
            for chunk in raw_chunks
        ]

        await create_document_chunks(chunk_models)

        return DocumentResponse(**created_document)

    except DocumentIngestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc