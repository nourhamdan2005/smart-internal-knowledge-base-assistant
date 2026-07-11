"""
DEVATTECH-121 / SP3-702: permanent guard against unauthenticated-endpoint
regressions. Walks every registered route in the app and asserts:

  - Any route NOT in _PUBLIC_ROUTES returns 401 when called with no
    Authorization header at all.
  - Any route under an admin-only prefix returns 403 when called with a
    valid token belonging to a plain "customer" role.

This does not replace endpoint-specific tests (ownership checks, business
logic, etc.) -- it only catches the specific regression class where a new
route is added and someone forgets Depends(get_current_user) / require_role.
"""
import re

import pytest

from app.main import app

# Routes that are deliberately public -- must match exactly (method, path).
# Path is the raw FastAPI path template, e.g. "/api/v1/auth/login".
_PUBLIC_ROUTES: set[tuple[str, str]] = {
    ("GET", "/health"),
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/refresh"),
}

# Any route whose path starts with one of these prefixes is admin-only
# (gated behind require_role(admin/compliance_officer) per ENGINEERING_RULES).
_ADMIN_PREFIXES = ("/api/v1/admin",)

# Methods we actually probe. HEAD/OPTIONS are excluded (framework-added,
# not app routes we own).
_METHODS_TO_CHECK = {"GET", "POST", "PUT", "DELETE", "PATCH"}

_PATH_PARAM_RE = re.compile(r"\{[^}]+\}")


@pytest.fixture
async def auth_tokens(client):
    """Register and login a plain customer test user, return tokens."""
    await client.post("/api/v1/auth/register", json={
        "full_name": "Security Matrix Test User",
        "email": "securitymatrixtest@neobank.com",
        "phone": "+96170000098",
        "password": "TestPass123",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "securitymatrixtest@neobank.com",
        "password": "TestPass123",
    })
    return response.json()


def _concrete_path(path_template: str) -> str:
    """Replace any {param} segment with a dummy value so the route resolves."""
    return _PATH_PARAM_RE.sub("1", path_template)


def _collect_routes() -> list[tuple[str, str]]:
    """
    Return (method, path_template) for every real endpoint in the app.

    Recursive because this FastAPI version wraps included routers in
    intermediate objects (_IncludedRouter -> original_router -> routes,
    possibly nested more than one level for sub-included routers) rather
    than flattening everything into app.routes directly.
    """
    collected: list[tuple[str, str]] = []
    seen: set[int] = set()

    def _walk(routes) -> None:
        for route in routes:
            if id(route) in seen:
                continue
            seen.add(id(route))

            path = getattr(route, "path", None)
            methods = getattr(route, "methods", None)
            if path and methods:
                for method in methods:
                    if method in _METHODS_TO_CHECK:
                        collected.append((method, path))
                continue  # a leaf APIRoute won't also have nested routes

            # Not a leaf route -- look for wherever the nested routes live.
            nested = getattr(route, "routes", None)
            if nested:
                _walk(nested)
                continue

            original_router = getattr(route, "original_router", None)
            if original_router is not None:
                nested = getattr(original_router, "routes", None)
                if nested:
                    _walk(nested)
                continue

    _walk(app.routes)
    return collected


_ALL_ROUTES = _collect_routes()
_NON_PUBLIC_ROUTES = [r for r in _ALL_ROUTES if r not in _PUBLIC_ROUTES]
_ADMIN_ROUTES = [
    r for r in _NON_PUBLIC_ROUTES if r[1].startswith(_ADMIN_PREFIXES)
]

assert _ALL_ROUTES, "Route collection returned nothing -- app.routes shape may have changed"
assert _NON_PUBLIC_ROUTES, "Expected at least one non-public route"
assert _ADMIN_ROUTES, "Expected at least one admin route -- check _ADMIN_PREFIXES"


@pytest.mark.parametrize(
    "method,path",
    _NON_PUBLIC_ROUTES,
    ids=[f"{m}_{p}" for m, p in _NON_PUBLIC_ROUTES],
)
async def test_route_requires_auth_when_unauthenticated(client, method, path):
    """Every non-whitelisted route must reject a request with no token at all."""
    url = _concrete_path(path)
    response = await client.request(method, url, json={} if method != "GET" else None)
    assert response.status_code == 401, (
        f"{method} {path} returned {response.status_code}, expected 401 "
        f"when called with no Authorization header. If this route is meant "
        f"to be public, add it to _PUBLIC_ROUTES in this file."
    )


@pytest.mark.parametrize(
    "method,path",
    _ADMIN_ROUTES,
    ids=[f"{m}_{p}" for m, p in _ADMIN_ROUTES],
)
async def test_admin_route_rejects_customer_role(client, method, path, auth_tokens):
    """Admin-only routes must return 403 for a valid but non-admin token."""
    url = _concrete_path(path)
    response = await client.request(
        method,
        url,
        json={} if method != "GET" else None,
        headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
    )
    assert response.status_code == 403, (
        f"{method} {path} returned {response.status_code} for a customer-role "
        f"token, expected 403."
    )
