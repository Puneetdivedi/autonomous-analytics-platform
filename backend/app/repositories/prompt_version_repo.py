"""PromptVersion repository."""

from __future__ import annotations

from sqlalchemy import select

from app.models.prompt_version import PromptVersion
from app.repositories.base import BaseRepository


class PromptVersionRepository(BaseRepository[PromptVersion]):
    model = PromptVersion

    async def get_active(self, agent_name: str) -> PromptVersion | None:
        """Return the active prompt version for ``agent_name`` or ``None``."""
        stmt = (
            select(PromptVersion)
            .where(
                PromptVersion.agent_name == agent_name,
                PromptVersion.is_active.is_(True),
            )
            .order_by(PromptVersion.version.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
