"""DataSource repository."""

from __future__ import annotations

from sqlalchemy import select

from app.models.datasource import DataSource
from app.repositories.base import BaseRepository


class DataSourceRepository(BaseRepository[DataSource]):
    model = DataSource

    async def list_for_project(self, project_id: str) -> list[DataSource]:
        """Return all data sources belonging to ``project_id``."""
        stmt = (
            select(DataSource)
            .where(DataSource.project_id == project_id)
            .order_by(DataSource.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
