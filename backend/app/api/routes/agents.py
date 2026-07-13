"""Agent observability routes — per-message execution records."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.api.deps import ActiveUser, DbSession
from app.repositories.agent_execution_repo import AgentExecutionRepository

router = APIRouter(tags=["agents"])


@router.get("/executions", summary="List agent executions for a message")
async def list_executions(message_id: str, db: DbSession, _: ActiveUser) -> list[dict[str, Any]]:
    rows = await AgentExecutionRepository(db).list_for_message(message_id)
    return [
        {
            "id": r.id,
            "node_name": r.node_name,
            "agent_name": r.agent_name,
            "status": r.status.value if hasattr(r.status, "value") else r.status,
            "attempt": r.attempt,
            "latency_ms": r.latency_ms,
            "prompt_tokens": r.prompt_tokens,
            "completion_tokens": r.completion_tokens,
            "cost_usd": r.cost_usd,
            "error": r.error,
            "created_at": r.created_at,
        }
        for r in rows
    ]
