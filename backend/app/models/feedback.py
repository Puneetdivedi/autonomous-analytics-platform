"""Feedback ORM model — user feedback on a message/answer."""

from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import FeedbackRating


class Feedback(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "feedback"

    message_id: Mapped[str] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    rating: Mapped[FeedbackRating] = mapped_column(
        Enum(FeedbackRating, native_enum=False, length=20), nullable=False
    )
    comment: Mapped[str | None] = mapped_column(Text)
    # Mirrored to LangFuse as a score.
    trace_id: Mapped[str | None] = mapped_column(Text)
