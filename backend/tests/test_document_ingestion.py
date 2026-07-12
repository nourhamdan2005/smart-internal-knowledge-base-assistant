from io import BytesIO

import pytest
from fastapi import UploadFile

from app.services import document_ingestion_service


@pytest.mark.asyncio
async def test_extract_text_from_valid_txt():
    file = UploadFile(
        filename="policy.txt",
        file=BytesIO(b"Employees may work remotely."),
    )

    result = await document_ingestion_service.extract_text_from_upload(file)

    assert result == "Employees may work remotely."


@pytest.mark.asyncio
async def test_extract_text_from_markdown():
    file = UploadFile(
        filename="policy.md",
        file=BytesIO(b"# Policy\n\nRemote work is allowed."),
    )

    result = await document_ingestion_service.extract_text_from_upload(file)

    assert result == "# Policy\n\nRemote work is allowed."


@pytest.mark.asyncio
async def test_extract_text_removes_utf8_bom():
    file = UploadFile(
        filename="policy.txt",
        file=BytesIO(
            b"\xef\xbb\xbfPassword Reset Guide"
        ),
    )

    result = await document_ingestion_service.extract_text_from_upload(file)

    assert result == "Password Reset Guide"


@pytest.mark.asyncio
async def test_extract_text_rejects_empty_file():
    file = UploadFile(
        filename="empty.txt",
        file=BytesIO(b""),
    )

    with pytest.raises(
        document_ingestion_service.DocumentIngestionError,
        match="empty",
    ):
        await document_ingestion_service.extract_text_from_upload(file)


@pytest.mark.asyncio
async def test_extract_text_rejects_unsupported_extension():
    file = UploadFile(
        filename="policy.csv",
        file=BytesIO(b"fake csv"),
    )

    with pytest.raises(
        document_ingestion_service.DocumentIngestionError,
        match="Unsupported file type",
    ):
        await document_ingestion_service.extract_text_from_upload(file)


def test_create_title_from_filename():
    result = document_ingestion_service.create_title_from_filename(
        "remote_work-policy.md"
    )

    assert result == "Remote Work Policy"


@pytest.mark.asyncio
async def test_process_uploaded_document_returns_create_schema():
    file = UploadFile(
        filename="remote_work-policy.md",
        file=BytesIO(b"Employees may work remotely."),
    )

    result = await document_ingestion_service.process_uploaded_document(
        file=file,
        category="HR",
        tags="remote, policy",
    )

    assert result.model_dump() == {
        "title": "Remote Work Policy",
        "category": "HR",
        "content": "Employees may work remotely.",
        "tags": ["remote", "policy"],
        "author": "Admin",
    }
