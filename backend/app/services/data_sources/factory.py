"""Factory for constructing the appropriate :class:`DataSourceAdapter`."""

from __future__ import annotations

from app.core.exceptions import DataSourceError
from app.core.logging import get_logger
from app.models.enums import DataSourceType
from app.services.data_sources.base import DataSourceAdapter
from app.services.data_sources.file_adapter import FileDataSourceAdapter
from app.services.data_sources.sql_adapter import SQLDataSourceAdapter

logger = get_logger(__name__)

_SQL_TYPES = {DataSourceType.POSTGRES, DataSourceType.MYSQL, DataSourceType.SQLITE}
_FILE_TYPES = {DataSourceType.CSV, DataSourceType.EXCEL}


def get_adapter(
    type: DataSourceType,
    *,
    connection_uri: str | None = None,
    file_path: str | None = None,
    sheet: str | int | None = None,
) -> DataSourceAdapter:
    """Return an adapter for the given data-source ``type``.

    SQL types require ``connection_uri``; file types require ``file_path``.
    Raises :class:`DataSourceError` on misconfiguration or unknown type.
    """
    if type in _SQL_TYPES:
        if not connection_uri:
            raise DataSourceError(f"'{type.value}' data source requires a connection_uri.")
        logger.info("adapter_created", type=type.value, kind="sql")
        return SQLDataSourceAdapter(connection_uri)

    if type in _FILE_TYPES:
        if not file_path:
            raise DataSourceError(f"'{type.value}' data source requires a file_path.")
        logger.info("adapter_created", type=type.value, kind="file")
        return FileDataSourceAdapter(file_path, type, sheet=sheet)

    raise DataSourceError(f"Unsupported data source type: {type}")


__all__ = ["get_adapter"]
