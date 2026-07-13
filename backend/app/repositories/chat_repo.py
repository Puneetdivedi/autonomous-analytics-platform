"""Chat repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.chat import Chat
from app.repositories.base import BaseRepository


class ChatRepository(BaseRepository[Chat]):
    model = Chat

    async def get_with_messages(self, chat_id: str) -> Chat | None:
        """Return the chat with its ``messages`` eagerly loaded, or ``None``."""
        stmt = (
            select(Chat)
            .where(Chat.id == chat_id)
            .options(selectinload(Chat.messages))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_project(self, project_id: str) -> list[Chat]:
        """Return all chats for ``project_id`` newest first."""
        stmt = (
            select(Chat)
            .where(Chat.project_id == project_id)
            .order_by(Chat.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
