"""Feedback service."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import Feedback
from app.repositories.feedback_repo import FeedbackRepository
from app.repositories.message_repo import MessageRepository
from app.schemas.report import FeedbackCreate


class FeedbackService:
    """Creates feedback for messages and lists it back."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.feedback = FeedbackRepository(session)
        self.messages = MessageRepository(session)

    async def create(self, data: FeedbackCreate, user_id: str) -> Feedback:
        """Create feedback attributed to ``user_id`` for a message.

        The referenced message must exist (raises :class:`NotFoundError`).
        """
        message = await self.messages.get_or_404(data.message_id)
        return await self.feedback.create(
            message_id=message.id,
            user_id=user_id,
            rating=data.rating,
            comment=data.comment,
            trace_id=message.trace_id,
        )

    async def list_for_message(self, message_id: str) -> list[Feedback]:
        """Return all feedback for a message."""
        return await self.feedback.list_for_message(message_id)
