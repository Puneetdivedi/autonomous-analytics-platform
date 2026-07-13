"""Domain and application exceptions.

These are provider-agnostic exceptions raised by the service/agent layers and
translated to HTTP responses by the exception-handling middleware.
"""

from __future__ import annotations


class AppError(Exception):
    """Base application error."""

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(AppError):
    status_code = 404
    error_code = "not_found"


class ConflictError(AppError):
    status_code = 409
    error_code = "conflict"


class ValidationError(AppError):
    status_code = 422
    error_code = "validation_error"


class AuthenticationError(AppError):
    status_code = 401
    error_code = "authentication_error"


class AuthorizationError(AppError):
    status_code = 403
    error_code = "authorization_error"


class RateLimitError(AppError):
    status_code = 429
    error_code = "rate_limit"


# --- Agent / graph domain errors ---


class AgentError(AppError):
    """Raised when an agent node fails irrecoverably."""

    status_code = 500
    error_code = "agent_error"


class SQLValidationError(AgentError):
    """Raised when generated SQL fails validation (unsafe or malformed)."""

    error_code = "sql_validation_error"


class SQLExecutionError(AgentError):
    error_code = "sql_execution_error"


class LLMError(AgentError):
    """Raised when all LLM providers (primary + fallback) fail."""

    error_code = "llm_error"


class DataSourceError(AppError):
    status_code = 400
    error_code = "datasource_error"
