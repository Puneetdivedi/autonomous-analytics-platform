"""Application configuration.

All settings are loaded from environment variables (or a local `.env`) using
Pydantic-Settings. This is the single source of truth for configuration and is
imported everywhere via the cached :func:`get_settings` accessor.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "staging", "production"]
LLMProvider = Literal["openai", "anthropic", "gemini", "groq", "ollama", "stub"]


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_name: str = "Enterprise Autonomous Analytics Platform"
    environment: Environment = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # --- Security ---
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    jwt_algorithm: str = "HS256"

    # --- Postgres ---
    database_url: str = "postgresql+asyncpg://eaap:eaap_password@localhost:5432/eaap"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Qdrant ---
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None

    # --- LLM ---
    llm_provider: LLMProvider = "openai"
    llm_model: str = "gpt-4o"
    llm_fallback_provider: LLMProvider = "anthropic"
    llm_fallback_model: str = "claude-sonnet-5"
    llm_temperature: float = 0.1
    llm_max_retries: int = 3

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    groq_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    # --- Embeddings ---
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"

    # --- LangFuse ---
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "http://localhost:3000"
    langfuse_enabled: bool = True

    # --- Agent graph ---
    max_graph_iterations: int = 25
    max_sql_rows: int = 10_000
    agent_node_timeout_seconds: int = 120

    # --- Storage ---
    upload_dir: str = "/data/uploads"
    report_dir: str = "/data/reports"
    max_upload_mb: int = 100

    @field_validator("backend_cors_origins")
    @classmethod
    def _strip_origins(cls, v: str) -> str:
        return v.strip()

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def sync_database_url(self) -> str:
        """Sync DSN for Alembic / tooling (strips asyncpg driver)."""
        return self.database_url.replace("+asyncpg", "").replace("+aiosqlite", "")


@lru_cache
def get_settings() -> Settings:
    """Return the cached singleton settings instance."""
    return Settings()


settings = get_settings()
