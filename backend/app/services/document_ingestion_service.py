from io import BytesIO
from pathlib import Path

from docx import Document
from fastapi import UploadFile
from pypdf import PdfReader

from app.schemas.document import DocumentCreate


SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".pdf",
    ".docx",
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


class DocumentIngestionError(Exception):
    """Raised when an uploaded document cannot be processed."""


def get_file_extension(filename: str | None) -> str:
    """
    Return the lowercase file extension.

    Example:
        policy.PDF -> .pdf
    """
    if not filename:
        return ""

    return Path(filename).suffix.lower()


def validate_file_extension(filename: str | None) -> str:
    """
    Validate that the uploaded file type is supported.
    """
    extension = get_file_extension(filename)

    if extension not in SUPPORTED_EXTENSIONS:
        raise DocumentIngestionError(
            "Unsupported file type. Only TXT, Markdown, PDF, and DOCX "
            "files are allowed."
        )

    return extension


def extract_text_from_txt_or_markdown(file_bytes: bytes) -> str:
    """
    Extract UTF-8 text from TXT or Markdown content.

    utf-8-sig removes an optional UTF-8 BOM.
    """
    try:
        return file_bytes.decode("utf-8-sig").strip()
    except UnicodeDecodeError as exc:
        raise DocumentIngestionError(
            "The uploaded text file must use UTF-8 encoding."
        ) from exc


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract readable text from all pages of a PDF.
    """
    try:
        reader = PdfReader(BytesIO(file_bytes))
    except Exception as exc:
        raise DocumentIngestionError(
            "The uploaded PDF file could not be read."
        ) from exc

    page_texts: list[str] = []

    for page in reader.pages:
        try:
            text = page.extract_text()
        except Exception:
            text = None

        if text and text.strip():
            page_texts.append(text.strip())

    extracted_text = "\n\n".join(page_texts).strip()

    if not extracted_text:
        raise DocumentIngestionError(
            "No readable text was found in the PDF. "
            "The file may be scanned or image-based."
        )

    return extracted_text


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text from DOCX paragraphs and tables.
    """
    try:
        document = Document(BytesIO(file_bytes))
    except Exception as exc:
        raise DocumentIngestionError(
            "The uploaded DOCX file could not be read."
        ) from exc

    extracted_parts: list[str] = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if text:
            extracted_parts.append(text)

    for table in document.tables:
        for row in table.rows:
            cell_values = [
                cell.text.strip()
                for cell in row.cells
                if cell.text.strip()
            ]

            if cell_values:
                extracted_parts.append(" | ".join(cell_values))

    extracted_text = "\n".join(extracted_parts).strip()

    if not extracted_text:
        raise DocumentIngestionError(
            "No readable text was found in the DOCX file."
        )

    return extracted_text


def extract_text_from_file(file_bytes: bytes, extension: str) -> str:
    """
    Choose the correct extractor according to the file extension.
    """
    if extension in {".txt", ".md"}:
        return extract_text_from_txt_or_markdown(file_bytes)

    if extension == ".pdf":
        return extract_text_from_pdf(file_bytes)

    if extension == ".docx":
        return extract_text_from_docx(file_bytes)

    raise DocumentIngestionError("Unsupported file type.")


async def extract_text_from_upload(file: UploadFile) -> str:
    """Validate an upload and return its extracted text."""
    extension = validate_file_extension(file.filename)
    file_bytes = await file.read()

    if not file_bytes:
        raise DocumentIngestionError("The uploaded file is empty.")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise DocumentIngestionError(
            "The uploaded file exceeds the maximum allowed size of 5 MB."
        )

    extracted_text = extract_text_from_file(
        file_bytes=file_bytes,
        extension=extension,
    )

    if not extracted_text.strip():
        raise DocumentIngestionError(
            "No readable text was found in the uploaded file."
        )

    return extracted_text


def generate_title_from_filename(filename: str | None) -> str:
    """
    Generate a readable title from a filename.

    Example:
        remote_work-policy.pdf -> Remote Work Policy
    """
    if not filename:
        return "Untitled Document"

    stem = Path(filename).stem
    normalized = stem.replace("_", " ").replace("-", " ")
    generated_title = " ".join(normalized.split()).title()

    return generated_title or "Untitled Document"


def create_title_from_filename(filename: str | None) -> str:
    """Backward-compatible alias for generating an upload title."""
    return generate_title_from_filename(filename)


def parse_tags(tags: str | None) -> list[str]:
    """
    Convert comma-separated tags into a clean list.

    Example:
        'remote, policy, employees'
        -> ['remote', 'policy', 'employees']
    """
    if not tags:
        return []

    parsed_tags: list[str] = []
    seen_tags: set[str] = set()

    for tag in tags.split(","):
        cleaned_tag = tag.strip()

        if not cleaned_tag:
            continue

        normalized_tag = cleaned_tag.lower()

        if normalized_tag in seen_tags:
            continue

        seen_tags.add(normalized_tag)
        parsed_tags.append(cleaned_tag)

    return parsed_tags


async def process_uploaded_document(
    file: UploadFile,
    category: str,
    title: str | None = None,
    tags: str | None = None,
    author: str = "Admin",
) -> DocumentCreate:
    """
    Validate an uploaded document, extract its text, and build the
    document data that will be stored in MongoDB.
    """
    extracted_text = await extract_text_from_upload(file)

    document_title = (
        title.strip()
        if title and title.strip()
        else generate_title_from_filename(file.filename)
    )

    return DocumentCreate(
        title=document_title,
        category=category.strip(),
        content=extracted_text,
        tags=parse_tags(tags),
        author=author.strip() or "Admin",
    )
