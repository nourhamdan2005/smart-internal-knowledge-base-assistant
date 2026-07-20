import pytest
from fastapi import FastAPI

from app import main
from app.main import app


def test_fastapi_application_loads_all_routes():
    assert isinstance(app, FastAPI)

    route_paths = set(app.openapi()["paths"])

    assert "/health" in route_paths
    assert "/uploads/" in route_paths
    assert "/query/" in route_paths
    assert "/auth/login" in route_paths
    assert "/auth/me" in route_paths
    assert "/users" in route_paths
    assert "/documents" in route_paths
    assert (
        "/maintenance/backfill-chunks"
        in route_paths
    )
    assert "/maintenance/backfill-vectors" in route_paths


@pytest.mark.asyncio
async def test_application_lifespan_creates_indexes(
    monkeypatch,
):
    index_creation_calls = 0

    async def fake_create_database_indexes():
        nonlocal index_creation_calls

        index_creation_calls += 1

        return {
            "documents": [],
            "document_chunks": [],
        }

    monkeypatch.setattr(
        main,
        "create_database_indexes",
        fake_create_database_indexes,
    )

    async with main.lifespan(main.app):
        assert index_creation_calls == 1

    assert index_creation_calls == 1
