from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.main import app
from app.schemas.user import UserRole


def principal(role):
    now = datetime.now(timezone.utc)
    return {
        "id": "64b7f11a8b1234567890abcd",
        "email": f"{role.value}@company.com",
        "full_name": f"{role.value.title()} User",
        "role": role,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
    }


def client_for(role):
    async def override_current_user():
        return principal(role)

    app.dependency_overrides[get_current_user] = (
        override_current_user
    )
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    yield
    app.dependency_overrides.clear()


def test_health_readiness_and_login_remain_public(monkeypatch):
    client = TestClient(app)

    async def database_ready():
        return True

    async def invalid_login(**kwargs):
        from app.services.auth_service import (
            InvalidCredentialsError,
        )

        raise InvalidCredentialsError(
            "Invalid email or password"
        )

    monkeypatch.setattr(
        "app.api.v1.endpoints.health.check_database_connection",
        database_ready,
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.auth.auth_service.login",
        invalid_login,
    )

    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
    assert client.post(
        "/auth/login",
        json={
            "email": "admin@company.com",
            "password": "wrong-password",
        },
    ).status_code == 401


def test_employee_can_query_and_view_documents(monkeypatch):
    async def query_documents(**kwargs):
        return {"answer": "Grounded answer", "sources": []}

    async def get_documents(**kwargs):
        return []

    monkeypatch.setattr(
        "app.api.v1.endpoints.query.query_documents",
        query_documents,
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.documents.document_service.get_documents",
        get_documents,
    )
    client = client_for(UserRole.EMPLOYEE)

    assert client.post(
        "/query/",
        json={"question": "What is the policy?"},
    ).status_code == 200
    assert client.get("/documents").status_code == 200
    assert client.get("/documents/documents").status_code == 200


def test_employee_cannot_upload_update_or_delete():
    client = client_for(UserRole.EMPLOYEE)

    upload = client.post(
        "/uploads/",
        files={"file": ("policy.txt", b"Policy content")},
        data={"category": "HR"},
    )
    update = client.patch(
        "/documents/64b7f11a8b1234567890abcd",
        json={"title": "Updated Policy"},
    )
    delete = client.delete(
        "/documents/64b7f11a8b1234567890abcd"
    )

    assert upload.status_code == 403
    assert update.status_code == 403
    assert delete.status_code == 403


def test_editor_can_upload(monkeypatch):
    from app.schemas.document import DocumentCreate

    now = datetime.now(timezone.utc)
    document = {
        "id": "64b7f11a8b1234567890abcd",
        "title": "Policy",
        "category": "HR",
        "content": "Long enough policy content.",
        "tags": [],
        "author": "Admin",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "original_filename": "policy.txt",
        "extension": ".txt",
        "mime_type": "text/plain",
        "file_size": 27,
        "checksum": "checksum",
        "uploaded_at": now,
    }

    async def process_uploaded_document(**kwargs):
        return DocumentCreate(
            title="Policy",
            category="HR",
            content="Long enough policy content.",
            checksum="checksum",
        )

    async def no_duplicate(checksum):
        return None

    async def create_document(document_data):
        return document

    monkeypatch.setattr(
        "app.api.v1.endpoints.uploads.process_uploaded_document",
        process_uploaded_document,
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.uploads.find_document_by_checksum",
        no_duplicate,
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.uploads.create_document",
        create_document,
    )
    client = client_for(UserRole.EDITOR)

    response = client.post(
        "/uploads/",
        files={"file": ("policy.txt", b"Policy content")},
        data={"category": "HR"},
    )

    assert response.status_code == 201


def test_editor_can_update_but_cannot_delete_or_maintain(
    monkeypatch,
):
    now = datetime.now(timezone.utc)
    document = {
        "id": "64b7f11a8b1234567890abcd",
        "title": "Updated Policy",
        "category": "HR",
        "content": "Long enough policy content.",
        "tags": [],
        "author": "Admin",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "original_filename": None,
        "extension": None,
        "mime_type": None,
        "file_size": None,
        "checksum": None,
        "uploaded_at": None,
    }

    async def update_document(*args, **kwargs):
        return document

    monkeypatch.setattr(
        "app.api.v1.endpoints.documents.document_service.update_document",
        update_document,
    )
    client = client_for(UserRole.EDITOR)

    assert client.patch(
        "/documents/64b7f11a8b1234567890abcd",
        json={"title": "Updated Policy"},
    ).status_code == 200
    assert client.delete(
        "/documents/64b7f11a8b1234567890abcd"
    ).status_code == 403
    assert client.post(
        "/maintenance/backfill-chunks"
    ).status_code == 403


def test_admin_can_run_maintenance(monkeypatch):
    async def backfill():
        return {
            "total_documents": 0,
            "processed_documents": 0,
            "skipped_documents": 0,
            "failed_documents": 0,
            "created_chunks": 0,
            "failures": [],
        }

    monkeypatch.setattr(
        "app.api.v1.endpoints.maintenance.backfill_missing_document_chunks",
        backfill,
    )
    client = client_for(UserRole.ADMIN)

    assert client.post(
        "/maintenance/backfill-chunks"
    ).status_code == 200


def test_admin_can_delete_document(monkeypatch):
    async def delete_document(document_id):
        return True

    monkeypatch.setattr(
        "app.api.v1.endpoints.documents.document_service.delete_document",
        delete_document,
    )
    client = client_for(UserRole.ADMIN)

    assert client.delete(
        "/documents/64b7f11a8b1234567890abcd"
    ).status_code == 204


def test_only_admin_can_manage_users(monkeypatch):
    now = datetime.now(timezone.utc)
    created_user = {
        "id": "64b7f11a8b1234567890abce",
        "email": "employee@company.com",
        "full_name": "Employee User",
        "role": UserRole.EMPLOYEE,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
    }

    async def create_user(user_data):
        return created_user

    monkeypatch.setattr(
        "app.api.v1.endpoints.users.auth_service.create_user",
        create_user,
    )
    payload = {
        "email": "employee@company.com",
        "full_name": "Employee User",
        "password": "password123",
        "role": "employee",
    }

    assert client_for(UserRole.EDITOR).post(
        "/users",
        json=payload,
    ).status_code == 403

    app.dependency_overrides.clear()

    response = client_for(UserRole.ADMIN).post(
        "/users",
        json=payload,
    )

    assert response.status_code == 201
    assert "hashed_password" not in response.json()


def test_auth_me_never_exposes_password_hash():
    client = client_for(UserRole.EMPLOYEE)

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert "hashed_password" not in response.json()
