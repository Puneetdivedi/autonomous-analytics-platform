"""Report service — listing and download resolution."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.report import Report
from app.repositories.report_repo import ReportRepository


class ReportService:
    """Lists generated reports and resolves file paths for download."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.reports = ReportRepository(session)

    async def list_for_project(self, project_id: str) -> list[Report]:
        """Return all reports for a project."""
        return await self.reports.list_for_project(project_id)

    async def get(self, report_id: str) -> Report:
        """Return a report or raise :class:`NotFoundError`."""
        return await self.reports.get_or_404(report_id)

    async def get_download_path(self, report_id: str) -> tuple[Report, Path]:
        """Return the report and its on-disk path, verifying the file exists."""
        report = await self.reports.get_or_404(report_id)
        path = Path(report.file_path)
        if not path.is_file():
            raise NotFoundError(
                "Report file is not available",
                details={"report_id": report_id},
            )
        return report, path
