"""Base agent abstraction.

Every specialized agent subclasses :class:`BaseAgent`. An agent is an LLM-backed
unit that:

* owns a versioned **system prompt**,
* produces a **structured output** (a Pydantic model) or free text,
* has **retry** with exponential backoff (tenacity),
* fails over to a **fallback LLM** (via the LLM factory),
* records **error handling** context for observability.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.exceptions import AgentError, LLMError
from app.core.llm import get_llm
from app.core.logging import get_logger

logger = get_logger(__name__)

TOut = TypeVar("TOut", bound=BaseModel)


class BaseAgent(Generic[TOut]):
    """Base class for structured-output agents."""

    #: Human-readable agent name (used in traces & AgentExecution records).
    name: str = "base"
    #: The Pydantic model the agent returns. Override in subclasses; ``None`` => text.
    output_schema: type[BaseModel] | None = None

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        self._llm = llm or get_llm()
        self._log = logger.bind(agent=self.name)

    # --- Prompt hooks -------------------------------------------------------

    def system_prompt(self, state: dict[str, Any]) -> str:
        """Return the system prompt for this invocation. Override in subclasses."""
        raise NotImplementedError

    def user_prompt(self, state: dict[str, Any]) -> str:
        """Return the user prompt for this invocation. Override in subclasses."""
        raise NotImplementedError

    # --- Core invocation ----------------------------------------------------

    async def run(self, state: dict[str, Any], **kwargs: Any) -> TOut | str:
        """Invoke the agent with retry + fallback and return its output."""

        @retry(
            retry=retry_if_exception_type((LLMError, Exception)),
            stop=stop_after_attempt(settings.llm_max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True,
        )
        async def _invoke() -> TOut | str:
            messages = [
                SystemMessage(content=self.system_prompt(state)),
                HumanMessage(content=self.user_prompt(state)),
            ]
            if self.output_schema is not None:
                structured = self._llm.with_structured_output(self.output_schema)
                result = await structured.ainvoke(messages, **kwargs)
                return result  # type: ignore[return-value]
            response = await self._llm.ainvoke(messages, **kwargs)
            return str(response.content)

        try:
            output = await _invoke()
            self._log.info("agent_completed")
            return output
        except Exception as exc:  # noqa: BLE001
            self._log.error("agent_failed", error=str(exc))
            raise AgentError(f"Agent '{self.name}' failed: {exc}") from exc
