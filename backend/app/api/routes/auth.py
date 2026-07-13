"""Authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import ActiveUser, DbSession
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter(tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(payload: RegisterRequest, db: DbSession) -> UserRead:
    """Create a new user account."""
    user = await AuthService(db).register(payload)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenPair, summary="Log in")
async def login(payload: LoginRequest, db: DbSession) -> TokenPair:
    """Exchange email + password for an access/refresh token pair."""
    return await AuthService(db).login(payload)


@router.post("/refresh", response_model=TokenPair, summary="Refresh tokens")
async def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    """Exchange a valid refresh token for a new token pair."""
    return await AuthService(db).refresh(payload.refresh_token)


@router.get("/me", response_model=UserRead, summary="Current user profile")
async def me(user: ActiveUser) -> UserRead:
    """Return the authenticated user's profile."""
    return UserRead.model_validate(user)
