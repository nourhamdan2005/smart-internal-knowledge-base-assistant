from pathlib import Path

from fastapi import UploadFile

from app.repositories.document_repository import create_document
from app.schemas.document import DocumentCreate


SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


class DocumentIngestionError(Exception):
    """Raised when an uploaded document cannot be processed."""


def get_file_extension(filename: str | None) -> str:
    if not filename:
        return ""

    return Path(filename).suffix.lower()


def create_title_from_filename(filename: str) -> str:
    """
    Convert a filename into a readable title.

    Example:
    remote_work_policy.md -> Remote Work Policy
    """
    stem = Path(filename).stem

    cleaned_title = stem.replace("_", " ").replace("-", " ").strip()

    if not cleaned_title:
        return "Uploaded Document"

    return cleaned_title.title()


async def extract_text_from_upload(file: UploadFile) -> str:
    extension = get_file_extension(file.filename)

    if extension not in SUPPORTED_EXTENSIONS:
        raise DocumentIngestionError(
            "Unsupported file type. Only TXT and Markdown files are allowed."
        )

    file_content = await file.read()

    if not file_content:
        raise DocumentIngestionError(
            "The uploaded file is empty."
        )

    if len(file_content) > MAX_FILE_SIZE:
        raise DocumentIngestionError(
            "The uploaded file exceeds the 5 MB size limit."
        )

    try:
        text = file_content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DocumentIngestionError(
            "The uploaded file must use UTF-8 text encoding."
        ) from exc

    cleaned_text = text.strip()

    if not cleaned_text:
        raise DocumentIngestionError(
            "The uploaded file does not contain readable text."
        )

    return cleaned_text


async def ingest_document(
    file: UploadFile,
    category: str,
    title: str | None = None,
    tags: list[str] | None = None,
    author: str = "Admin",
) -> dict:
    content = await extract_text_from_upload(file)

    document_title = (
        title.strip()
        if title and title.strip()
        else create_title_from_filename(file.filename or "")
    )

    normalized_tags = [
        tag.strip()
        for tag in (tags or [])
        if tag.strip()
    ]

    document_data = DocumentCreate(
        title=document_title,
        category=category,
        content=content,
        tags=normalized_tags,
        author=author,
    )

    return await create_document(document_data)