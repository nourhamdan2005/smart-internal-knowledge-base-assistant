from collections.abc import Awaitable, Callable
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.core.config import settings
from app.core.security import (
    AuthenticationError,
    SecurityConfigurationError,
    decode_access_token,
)
from app.repositories import user_repository
from app.repositories.user_repository import UserRepositoryError
from app.schemas.user import UserRole
from app.services.auth_service import development_principal


bearer_scheme = HTTPBearer(auto_error=False)
AUTHENTICATION_HEADERS = {"WWW-Authenticate": "Bearer"}


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers=AUTHENTICATION_HEADERS,
    )


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ] = None,
) -> dict[str, Any]:
    """Load the authoritative current user from MongoDB."""
    if not settings.auth_enabled:
        return development_principal()

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise authentication_error()

    try:
        payload = decode_access_token(credentials.credentials)
    except (AuthenticationError, SecurityConfigurationError) as exc:
        raise authentication_error() from exc

    try:
        user = await user_repository.get_by_id(payload["sub"])
    except UserRepositoryError as exc:
        raise authentication_error() from exc

    if user is None or not user["is_active"]:
        raise authentication_error()

    return user


CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]


def require_roles(
    *roles: UserRole,
) -> Callable[..., Awaitable[dict[str, Any]]]:
    allowed_roles = set(roles)

    async def role_dependency(
        current_user: CurrentUser,
    ) -> dict[str, Any]:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_dependency


require_authenticated = require_roles(
    UserRole.ADMIN,
    UserRole.EDITOR,
    UserRole.EMPLOYEE,
)
require_admin = require_roles(UserRole.ADMIN)
require_editor_or_admin = require_roles(
    UserRole.ADMIN,
    UserRole.EDITOR,
)
