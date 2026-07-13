"""Feedback repository."""

from __future__ import annotations

from sqlalchemy import select

from app.models.feedback import Feedback
from app.repositories.base import BaseRepository


class FeedbackRepository(BaseRepository[Feedback]):
    model = Feedback

    async def list_for_message(self, message_id: str) -> list[Feedback]:
        """Return all feedback rows for ``message_id`` newest first."""
        stmt = (
            select(Feedback)
            .where(Feedback.message_id == message_id)
            .order_by(Feedback.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
