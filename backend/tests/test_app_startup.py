from fastapi import FastAPI

from app.main import app


def test_fastapi_application_loads_all_routes():
    assert isinstance(app, FastAPI)

    route_paths = set(app.openapi()["paths"])

    assert "/health" in route_paths
    assert "/uploads/" in route_paths
    assert "/query/" in route_paths
    assert (
        "/maintenance/backfill-chunks"
        in route_paths
    )
