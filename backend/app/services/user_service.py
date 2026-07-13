"""User profile service."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserUpdate


class UserService:
    """Read/update user profiles and list users (admin)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def get(self, user_id: str) -> User:
        """Return the user or raise :class:`NotFoundError`."""
        return await self.users.get_or_404(user_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[User]:
        """Return a page of users (admin use)."""
        return await self.users.list(limit=limit, offset=offset, order_by=User.created_at.desc())

    async def count(self) -> int:
        return await self.users.count()

    async def update(self, user_id: str, data: UserUpdate) -> User:
        """Apply a partial update to a user profile."""
        user = await self.users.get_or_404(user_id)
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return user
        return await self.users.update(user, **changes)
