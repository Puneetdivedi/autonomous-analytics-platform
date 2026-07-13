"""DataSource schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import DataSourceType
from app.schemas.common import TimestampedSchema


class DataSourceConnectionCreate(BaseModel):
    """Register an external database connection."""

    project_id: str
    name: str = Field(min_length=1, max_length=255)
    type: DataSourceType
    connection_uri: str


class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool = True


class TableSchema(BaseModel):
    table: str
    columns: list[ColumnInfo]
    row_estimate: int | None = None


class DataSourceRead(TimestampedSchema):
    project_id: str
    name: str
    type: DataSourceType
    connection_uri: str | None
    file_path: str | None
    schema_cache: dict | None
