"""Report routes: listing and download."""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from app.api.deps import ActiveUser, DbSession
from app.models.enums import ReportFormat
from app.schemas.report import ReportRead
from app.services.report_service import ReportService

router = APIRouter(tags=["reports"])

_MEDIA_TYPES = {
    ReportFormat.PDF: "application/pdf",
    ReportFormat.DOCX: ("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ReportFormat.XLSX: ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
}


@router.get("", response_model=list[ReportRead], summary="List reports")
async def list_reports(
    db: DbSession,
    _user: ActiveUser,
    project_id: str = Query(...),
) -> list[ReportRead]:
    """List all reports generated for a project."""
    reports = await ReportService(db).list_for_project(project_id)
    return [ReportRead.model_validate(r) for r in reports]


@router.get("/{report_id}/download", summary="Download a report file")
async def download_report(
    report_id: str,
    db: DbSession,
    _user: ActiveUser,
) -> FileResponse:
    """Stream the generated report file as an attachment."""
    report, path = await ReportService(db).get_download_path(report_id)
    media_type = _MEDIA_TYPES.get(report.format, "application/octet-stream")
    filename = f"{report.title}.{report.format.value}"
    return FileResponse(path=path, media_type=media_type, filename=filename)
