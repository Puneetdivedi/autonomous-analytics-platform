"""Data source routes: connections, uploads and introspection."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Form, Query, UploadFile, status

from app.api.deps import ActiveUser, DbSession
from app.core.exceptions import DataSourceError
from app.models.enums import DataSourceType
from app.schemas.datasource import DataSourceConnectionCreate, DataSourceRead
from app.services.datasource_service import DataSourceService

router = APIRouter(tags=["datasources"])

_EXTENSION_TYPES = {
    ".csv": DataSourceType.CSV,
    ".xlsx": DataSourceType.EXCEL,
    ".xls": DataSourceType.EXCEL,
    ".sqlite": DataSourceType.SQLITE,
    ".db": DataSourceType.SQLITE,
}


def _infer_type(filename: str, explicit: str | None) -> DataSourceType:
    if explicit:
        try:
            return DataSourceType(explicit.lower())
        except ValueError as exc:
            raise DataSourceError(
                f"Unsupported data source type: {explicit}"
            ) from exc
    suffix = Path(filename).suffix.lower()
    inferred = _EXTENSION_TYPES.get(suffix)
    if inferred is None:
        raise DataSourceError(
            f"Cannot infer data source type from file '{filename}'"
        )
    return inferred


@router.post(
    "/connections",
    response_model=DataSourceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a database connection",
)
async def create_connection(
    payload: DataSourceConnectionCreate,
    db: DbSession,
    _user: ActiveUser,
) -> DataSourceRead:
    """Register an external database connection for a project."""
    ds = await DataSourceService(db).register_connection(payload)
    return DataSourceRead.model_validate(ds)


@router.post(
    "/upload",
    response_model=DataSourceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a data file",
)
async def upload_datasource(
    db: DbSession,
    _user: ActiveUser,
    project_id: str = Form(...),
    file: UploadFile = File(...),
    type: str | None = Form(default=None),
) -> DataSourceRead:
    """Upload a CSV/Excel/SQLite file and register it as a data source."""
    content = await file.read()
    ds_type = _infer_type(file.filename or "upload", type)
    ds = await DataSourceService(db).save_upload(
        project_id=project_id,
        filename=file.filename or "upload",
        content=content,
        type=ds_type,
    )
    return DataSourceRead.model_validate(ds)


@router.get("", response_model=list[DataSourceRead], summary="List data sources")
async def list_datasources(
    db: DbSession,
    _user: ActiveUser,
    project_id: str = Query(...),
) -> list[DataSourceRead]:
    """List all data sources for a project."""
    items = await DataSourceService(db).list_for_project(project_id)
    return [DataSourceRead.model_validate(d) for d in items]


@router.post(
    "/{datasource_id}/introspect",
    response_model=DataSourceRead,
    summary="Introspect a data source schema",
)
async def introspect_datasource(
    datasource_id: str,
    db: DbSession,
    _user: ActiveUser,
) -> DataSourceRead:
    """Introspect and cache the schema for a data source."""
    ds = await DataSourceService(db).introspect(datasource_id)
    return DataSourceRead.model_validate(ds)
