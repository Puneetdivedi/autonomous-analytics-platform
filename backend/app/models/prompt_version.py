"""PromptVersion ORM model — versioned agent system prompts."""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDMixin


class PromptVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "prompt_versions"
    __table_args__ = (UniqueConstraint("agent_name", "version", name="uq_prompt_agent_version"),)

    agent_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
