"""User management routes."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import AdminUser, DbSession
from app.schemas.common import Page
from app.schemas.user import UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(tags=["users"])


@router.get(
    "",
    response_model=Page[UserRead],
    summary="List users (admin)",
)
async def list_users(
    db: DbSession,
    _admin: AdminUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
) -> Page[UserRead]:
    """List all users. Requires administrator privileges."""
    service = UserService(db)
    users = await service.list(limit=size, offset=(page - 1) * size)
    total = await service.count()
    return Page[UserRead](
        items=[UserRead.model_validate(u) for u in users],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{user_id}", response_model=UserRead, summary="Get a user (admin)")
async def get_user(user_id: str, db: DbSession, _admin: AdminUser) -> UserRead:
    """Fetch a single user by id. Requires administrator privileges."""
    user = await UserService(db).get(user_id)
    return UserRead.model_validate(user)


@router.patch("/{user_id}", response_model=UserRead, summary="Update a user (admin)")
async def update_user(
    user_id: str,
    payload: UserUpdate,
    db: DbSession,
    _admin: AdminUser,
) -> UserRead:
    """Apply a partial update to a user. Requires administrator privileges."""
    user = await UserService(db).update(user_id, payload)
    return UserRead.model_validate(user)
