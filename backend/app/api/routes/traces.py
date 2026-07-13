"""Trace routes — surface LangFuse trace info tied to a message/execution."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.api.deps import ActiveUser, DbSession
from app.core.config import settings
from app.repositories.agent_execution_repo import AgentExecutionRepository
from app.repositories.message_repo import MessageRepository

router = APIRouter(tags=["traces"])


@router.get("", summary="Trace summary for a message")
async def trace_summary(message_id: str, db: DbSession, _: ActiveUser) -> dict[str, Any]:
    msg = await MessageRepository(db).get(message_id)
    execs = await AgentExecutionRepository(db).list_for_message(message_id)
    total_latency = sum(e.latency_ms or 0 for e in execs)
    total_tokens = sum((e.prompt_tokens or 0) + (e.completion_tokens or 0) for e in execs)
    total_cost = sum(e.cost_usd or 0 for e in execs)
    trace_id = msg.trace_id if msg else None
    return {
        "trace_id": trace_id,
        "message_id": message_id,
        "langfuse_url": f"{settings.langfuse_host}/trace/{trace_id}" if trace_id else None,
        "spans": [
            {
                "node_name": e.node_name,
                "agent_name": e.agent_name,
                "status": e.status.value if hasattr(e.status, "value") else e.status,
                "latency_ms": e.latency_ms,
                "attempt": e.attempt,
                "error": e.error,
            }
            for e in execs
        ],
        "totals": {
            "latency_ms": round(total_latency, 1),
            "tokens": total_tokens,
            "cost_usd": round(total_cost, 6),
            "node_count": len(execs),
            "error_count": sum(1 for e in execs if e.error),
        },
    }


@router.get("/{trace_id}", summary="Trace detail passthrough")
async def trace_detail(trace_id: str, _: ActiveUser) -> dict[str, Any]:
    return {
        "trace_id": trace_id,
        "langfuse_url": f"{settings.langfuse_host}/trace/{trace_id}",
    }
