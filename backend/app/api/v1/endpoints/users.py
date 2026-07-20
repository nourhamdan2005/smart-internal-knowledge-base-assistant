from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies.auth import require_admin
from app.repositories.user_repository import (
    DuplicateUserEmailError,
    UserRepositoryError,
)
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services import auth_service


router = APIRouter(prefix="/users", tags=["Users"])


def map_user_error(exc: Exception) -> HTTPException:
    if isinstance(exc, DuplicateUserEmailError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    if isinstance(exc, auth_service.UserNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if isinstance(
        exc,
        auth_service.UserOperationForbiddenError,
    ):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="User storage is temporarily unavailable.",
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_data: UserCreate,
    _current_user=Depends(require_admin),
) -> UserResponse:
    try:
        user = await auth_service.create_user(user_data)
    except (DuplicateUserEmailError, UserRepositoryError) as exc:
        raise map_user_error(exc) from exc

    return UserResponse(**user)


@router.get("", response_model=list[UserResponse])
async def list_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    _current_user=Depends(require_admin),
) -> list[UserResponse]:
    try:
        users = await auth_service.list_users(
            page=page,
            limit=limit,
        )
    except UserRepositoryError as exc:
        raise map_user_error(exc) from exc

    return [UserResponse(**user) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    _current_user=Depends(require_admin),
) -> UserResponse:
    try:
        user = await auth_service.get_user(user_id)
    except (
        UserRepositoryError,
        auth_service.UserNotFoundError,
    ) as exc:
        raise map_user_error(exc) from exc

    return UserResponse(**user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user=Depends(require_admin),
) -> UserResponse:
    try:
        user = await auth_service.update_user(
            user_id=user_id,
            user_data=user_data,
            acting_user_id=current_user["id"],
        )
    except (
        DuplicateUserEmailError,
        UserRepositoryError,
        auth_service.UserNotFoundError,
        auth_service.UserOperationForbiddenError,
    ) as exc:
        raise map_user_error(exc) from exc

    return UserResponse(**user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deactivate_user(
    user_id: str,
    current_user=Depends(require_admin),
) -> None:
    try:
        await auth_service.deactivate_user(
            user_id=user_id,
            acting_user_id=current_user["id"],
        )
    except (
        UserRepositoryError,
        auth_service.UserNotFoundError,
        auth_service.UserOperationForbiddenError,
    ) as exc:
        raise map_user_error(exc) from exc

    return None
