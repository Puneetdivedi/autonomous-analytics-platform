"""Lightweight token/cost accounting used to enrich AgentExecution records."""

from __future__ import annotations

from dataclasses import dataclass

# Approximate USD per 1K tokens (input, output). Extend as needed.
_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (0.0025, 0.010),
    "gpt-4o-mini": (0.00015, 0.0006),
    "claude-sonnet-5": (0.003, 0.015),
    "claude-opus-4-8": (0.015, 0.075),
    "gemini-1.5-pro": (0.00125, 0.005),
    "llama-3.1-70b": (0.0, 0.0),
}


@dataclass(slots=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens


def estimate_cost(model: str, usage: TokenUsage) -> float:
    """Estimate USD cost for a completion given model and token usage."""
    in_rate, out_rate = _PRICING.get(model, (0.0, 0.0))
    return round(
        (usage.prompt_tokens / 1000) * in_rate + (usage.completion_tokens / 1000) * out_rate,
        6,
    )


def extract_usage(response: object) -> TokenUsage:
    """Best-effort extraction of token usage from a LangChain AIMessage."""
    meta = getattr(response, "usage_metadata", None) or {}
    if meta:
        return TokenUsage(
            prompt_tokens=int(meta.get("input_tokens", 0)),
            completion_tokens=int(meta.get("output_tokens", 0)),
        )
    resp_meta = getattr(response, "response_metadata", {}) or {}
    token_usage = resp_meta.get("token_usage") or resp_meta.get("usage") or {}
    return TokenUsage(
        prompt_tokens=int(token_usage.get("prompt_tokens", 0)),
        completion_tokens=int(token_usage.get("completion_tokens", 0)),
    )
