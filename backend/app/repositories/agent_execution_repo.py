"""AgentExecution repository."""

from __future__ import annotations

from sqlalchemy import select

from app.models.agent_execution import AgentExecution
from app.repositories.base import BaseRepository


class AgentExecutionRepository(BaseRepository[AgentExecution]):
    model = AgentExecution

    async def list_for_message(self, message_id: str) -> list[AgentExecution]:
        """Return all node executions for ``message_id`` in creation order."""
        stmt = (
            select(AgentExecution)
            .where(AgentExecution.message_id == message_id)
            .order_by(AgentExecution.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
