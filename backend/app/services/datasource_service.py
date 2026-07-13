"""DataSource service — connection registration, uploads and introspection."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import anyio.to_thread
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import DataSourceError
from app.core.logging import get_logger
from app.models.datasource import DataSource
from app.models.enums import DataSourceType
from app.repositories.datasource_repo import DataSourceRepository
from app.repositories.project_repo import ProjectRepository
from app.schemas.datasource import DataSourceConnectionCreate

logger = get_logger(__name__)


class DataSourceService:
    """Registers DB connections and file uploads, and introspects schemas."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.datasources = DataSourceRepository(session)
        self.projects = ProjectRepository(session)

    async def register_connection(self, data: DataSourceConnectionCreate) -> DataSource:
        """Register an external database connection for a project."""
        await self.projects.get_or_404(data.project_id)
        return await self.datasources.create(
            project_id=data.project_id,
            name=data.name,
            type=data.type,
            connection_uri=data.connection_uri,
        )

    async def list_for_project(self, project_id: str) -> list[DataSource]:
        """Return all data sources for a project."""
        return await self.datasources.list_for_project(project_id)

    async def get(self, datasource_id: str) -> DataSource:
        """Return a data source or raise :class:`NotFoundError`."""
        return await self.datasources.get_or_404(datasource_id)

    async def save_upload(
        self,
        project_id: str,
        filename: str,
        content: bytes,
        type: DataSourceType,
    ) -> DataSource:
        """Persist an uploaded file under ``settings.upload_dir``.

        Enforces ``settings.max_upload_mb`` and rejects empty uploads. Returns
        the created :class:`DataSource` pointing at the stored file.
        """
        await self.projects.get_or_404(project_id)

        if not content:
            raise DataSourceError("Uploaded file is empty")

        max_bytes = settings.max_upload_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise DataSourceError(
                f"File exceeds maximum size of {settings.max_upload_mb} MB",
                details={"size_bytes": len(content), "max_bytes": max_bytes},
            )

        safe_name = os.path.basename(filename) or "upload"
        project_dir = Path(settings.upload_dir) / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        stored_path = project_dir / f"{uuid.uuid4().hex}_{safe_name}"

        try:
            stored_path.write_bytes(content)
        except OSError as exc:
            raise DataSourceError(
                "Failed to store uploaded file",
                details={"reason": str(exc)},
            ) from exc

        return await self.datasources.create(
            project_id=project_id,
            name=safe_name,
            type=type,
            file_path=str(stored_path),
        )

    async def introspect(self, datasource_id: str) -> DataSource:
        """Introspect and cache the data source schema.

        Uses the adapter factory (imported lazily) to discover tables/columns
        and stores them under ``schema_cache`` as ``{"tables": [...]}``. If the
        adapter layer is not importable, an empty schema is stored so callers
        always get a consistent shape.
        """
        ds = await self.datasources.get_or_404(datasource_id)

        schema: dict = {"tables": []}
        try:
            from app.services.data_sources.factory import (  # noqa: PLC0415
                get_adapter,
            )
        except Exception as exc:  # noqa: BLE001 — adapter layer optional
            logger.warning(
                "datasource.introspect.adapter_unavailable",
                datasource_id=datasource_id,
                error=str(exc),
            )
        else:
            try:
                adapter = get_adapter(
                    ds.type,
                    connection_uri=ds.connection_uri,
                    file_path=ds.file_path,
                )
                try:
                    # Adapter methods are synchronous — run off the event loop.
                    tables = await anyio.to_thread.run_sync(adapter.introspect_schema)
                finally:
                    adapter.close()
                schema = {"tables": [t.model_dump() for t in tables]}
            except DataSourceError:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "datasource.introspect.failed",
                    datasource_id=datasource_id,
                    error=str(exc),
                )
                raise DataSourceError(
                    "Failed to introspect data source",
                    details={"reason": str(exc)},
                ) from exc

        return await self.datasources.update(ds, schema_cache=schema)
