"""Project repository."""

from __future__ import annotations

from sqlalchemy import select

from app.models.project import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    model = Project

    async def list_for_owner(self, owner_id: str) -> list[Project]:
        """Return all projects owned by ``owner_id`` newest first."""
        stmt = (
            select(Project)
            .where(Project.owner_id == owner_id)
            .order_by(Project.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
