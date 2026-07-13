"""Project ORM model — groups data sources, chats and reports."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.chat import Chat
    from app.models.datasource import DataSource
    from app.models.report import Report
    from app.models.user import User


class Project(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    owner: Mapped[User] = relationship(back_populates="projects")
    data_sources: Mapped[list[DataSource]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    chats: Mapped[list[Chat]] = relationship(back_populates="project", cascade="all, delete-orphan")
    reports: Mapped[list[Report]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
