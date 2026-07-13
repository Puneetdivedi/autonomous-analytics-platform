"""Report ORM model — a generated downloadable artifact."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import ReportFormat

if TYPE_CHECKING:
    from app.models.project import Project


class Report(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "reports"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    message_id: Mapped[str | None] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[ReportFormat] = mapped_column(
        Enum(ReportFormat, native_enum=False, length=10), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    # Structured summary used to render the report (insights, charts, stats).
    payload: Mapped[dict | None] = mapped_column(JSON)

    project: Mapped[Project] = relationship(back_populates="reports")
