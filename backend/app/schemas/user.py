from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRole(StrEnum):
    ADMIN = "admin"
    EDITOR = "editor"
    EMPLOYEE = "employee"


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=150)
    password: str = Field(..., min_length=8, max_length=1024)
    role: UserRole = UserRole.EMPLOYEE

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=1024,
    )
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(
        cls,
        value: EmailStr | None,
    ) -> str | None:
        if value is None:
            return None

        return str(value).strip().lower()


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None


class CurrentUserResponse(UserResponse):
    pass


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=1024)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
