"""Message repository."""

from __future__ import annotations

from sqlalchemy import select

from app.models.message import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    model = Message

    async def list_for_chat(self, chat_id: str) -> list[Message]:
        """Return all messages in ``chat_id`` in chronological order."""
        stmt = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
