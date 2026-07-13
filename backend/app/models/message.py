"""Message ORM model — a single turn in a chat."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import MessageRole

if TYPE_CHECKING:
    from app.models.agent_execution import AgentExecution
    from app.models.chat import Chat


class Message(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "messages"

    chat_id: Mapped[str] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, native_enum=False, length=20), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # Rich structured payload: sql, charts, statistics, recommendations, etc.
    artifacts: Mapped[dict | None] = mapped_column(JSON)
    # LangFuse trace id linking this turn to its full agent trace.
    trace_id: Mapped[str | None] = mapped_column(Text)

    chat: Mapped[Chat] = relationship(back_populates="messages")
    executions: Mapped[list[AgentExecution]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )
