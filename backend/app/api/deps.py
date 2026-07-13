"""Shared FastAPI dependencies: authentication and role guards."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.database.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repo import UserRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login",
    auto_error=False,
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
) -> User:
    """Resolve the authenticated user from a Bearer access token."""
    from app.core.security import decode_token  # local import avoids cycles

    if not token:
        raise AuthenticationError("Not authenticated")

    payload = decode_token(token, expected_type="access")
    subject = payload.get("sub")
    if not subject:
        raise AuthenticationError("Invalid authentication token")

    user = await UserRepository(db).get(subject)
    if user is None:
        raise AuthenticationError("User no longer exists")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_active_user(user: CurrentUser) -> User:
    """Ensure the authenticated user's account is active."""
    if not user.is_active:
        raise AuthenticationError("Inactive user")
    return user


ActiveUser = Annotated[User, Depends(get_current_active_user)]


def require_roles(
    *roles: UserRole,
) -> Callable[[User], Coroutine[Any, Any, User]]:
    """Return a dependency enforcing the user holds one of ``roles``.

    Superusers always pass.
    """
    allowed = {r.value for r in roles}

    async def _guard(user: ActiveUser) -> User:
        if user.is_superuser or user.role.value in allowed:
            return user
        raise AuthorizationError("Insufficient permissions")

    return _guard


async def require_admin(user: ActiveUser) -> User:
    """Dependency requiring admin role (or superuser)."""
    if user.is_superuser or user.role == UserRole.ADMIN:
        return user
    raise AuthorizationError("Administrator privileges required")


AdminUser = Annotated[User, Depends(require_admin)]
