from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import SecurityConfigurationError
from app.dependencies.auth import get_current_user
from app.schemas.user import (
    CurrentUserResponse,
    LoginRequest,
    TokenResponse,
)
from app.services import auth_service
from app.repositories.user_repository import UserRepositoryError


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    try:
        result = await auth_service.login(
            email=str(request.email),
            password=request.password,
        )
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except SecurityConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured.",
        ) from exc
    except UserRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is temporarily unavailable.",
        ) from exc

    return TokenResponse(**result)


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(
    current_user=Depends(get_current_user),
) -> CurrentUserResponse:
    return CurrentUserResponse(
        **auth_service.public_user(current_user)
    )
