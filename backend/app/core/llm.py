"""LLM factory with multi-provider support and fallback.

Provides a single entry point for constructing chat models from any configured
provider (OpenAI, Anthropic, Gemini, Groq, Ollama) plus a resilient wrapper that
transparently fails over to a secondary provider when the primary errors.
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel

from app.core.config import LLMProvider, settings
from app.core.exceptions import LLMError
from app.core.logging import get_logger

logger = get_logger(__name__)


def _build_model(provider: LLMProvider, model: str, **kwargs: Any) -> BaseChatModel:
    """Instantiate a chat model for the given provider."""
    temperature = kwargs.pop("temperature", settings.llm_temperature)

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=settings.openai_api_key,
            max_retries=settings.llm_max_retries,
            **kwargs,
        )
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=settings.anthropic_api_key,
            max_retries=settings.llm_max_retries,
            **kwargs,
        )
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=settings.google_api_key,
            **kwargs,
        )
    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=model,
            temperature=temperature,
            api_key=settings.groq_api_key,
            **kwargs,
        )
    if provider == "ollama":
        from langchain_community.chat_models import ChatOllama

        return ChatOllama(
            model=model,
            temperature=temperature,
            base_url=settings.ollama_base_url,
            **kwargs,
        )
    raise LLMError(f"Unsupported LLM provider: {provider}")


def get_llm(
    *,
    provider: LLMProvider | None = None,
    model: str | None = None,
    with_fallback: bool = True,
    **kwargs: Any,
) -> BaseChatModel:
    """Return a chat model, optionally wrapped with a fallback provider.

    LangChain's ``with_fallbacks`` gives us graceful recovery: if the primary
    model raises, the secondary provider is tried automatically.
    """
    provider = provider or settings.llm_provider
    model = model or settings.llm_model

    # Dependency-free stub for local demos / tests (no API key, no network).
    if provider == "stub":
        from app.core.stub_llm import StubChatModel

        return StubChatModel()  # type: ignore[return-value]

    primary = _build_model(provider, model, **kwargs)

    if not with_fallback:
        return primary

    try:
        fallback = _build_model(
            settings.llm_fallback_provider, settings.llm_fallback_model, **kwargs
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("fallback_llm_unavailable", error=str(exc))
        return primary

    return primary.with_fallbacks([fallback])
