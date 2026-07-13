"""Report repository."""

from __future__ import annotations

from sqlalchemy import select

from app.models.report import Report
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    model = Report

    async def list_for_project(self, project_id: str) -> list[Report]:
        """Return all reports for ``project_id`` newest first."""
        stmt = (
            select(Report).where(Report.project_id == project_id).order_by(Report.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
