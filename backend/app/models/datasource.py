"""DataSource ORM model — a connected DB or uploaded file."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import DataSourceType

if TYPE_CHECKING:
    from app.models.project import Project


class DataSource(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "data_sources"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[DataSourceType] = mapped_column(
        Enum(DataSourceType, native_enum=False, length=20), nullable=False
    )
    # For files: absolute path. For DBs: connection URI (secrets encrypted upstream).
    connection_uri: Mapped[str | None] = mapped_column(String(1024))
    file_path: Mapped[str | None] = mapped_column(String(1024))
    # Cached, introspected schema: {table: [{name, type, nullable}, ...]}
    schema_cache: Mapped[dict | None] = mapped_column(JSON)

    project: Mapped["Project"] = relationship(back_populates="data_sources")
