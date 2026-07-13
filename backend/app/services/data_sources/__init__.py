"""Data-source adapters.

A uniform interface over SQL databases and uploaded files. Construct adapters
via :func:`get_adapter` rather than instantiating concrete classes directly.
"""

from __future__ import annotations

from app.services.data_sources.base import DataSourceAdapter
from app.services.data_sources.factory import get_adapter
from app.services.data_sources.file_adapter import FileDataSourceAdapter
from app.services.data_sources.sql_adapter import SQLDataSourceAdapter

__all__ = [
    "DataSourceAdapter",
    "SQLDataSourceAdapter",
    "FileDataSourceAdapter",
    "get_adapter",
]
