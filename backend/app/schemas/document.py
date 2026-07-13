from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


DocumentCategory = Literal[
    "HR",
    "IT",
    "Engineering",
    "API Docs",
    "Deployment",
    "Security",
    "Testing",
    "Onboarding",
    "Project Management",
]


class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    category: DocumentCategory
    content: str = Field(..., min_length=10)
    tags: list[str] = []
    author: str = Field(default="Admin", max_length=100)
    original_filename: str | None = None
    extension: str | None = None
    mime_type: str | None = None
    file_size: int | None = Field(default=None, ge=0)
    checksum: str | None = None
    uploaded_at: datetime | None = None


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=150)
    category: DocumentCategory | None = None
    content: str | None = Field(default=None, min_length=10)
    tags: list[str] | None = None
    author: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None


class DocumentResponse(BaseModel):
    id: str
    title: str
    category: DocumentCategory
    content: str
    tags: list[str]
    author: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    original_filename: str | None = None
    extension: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    checksum: str | None = None
    uploaded_at: datetime | None = None
