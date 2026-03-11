"""Configuration for Cherry Evals using pydantic-settings."""

import logging
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_config_logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Google GenAI API (embeddings + light LLM tasks)
    google_api_key: str = ""
    google_genai_use_vertexai: int = 0

    # Anthropic API (reasoning tasks)
    anthropic_api_key: str = ""

    # Cerebras API (fast inference)
    cerebras_api_key: str = ""

    # Database connections
    database_url: str = "postgresql://cherry:cherry@localhost:5433/cherry_evals"
    qdrant_url: str = "http://localhost:6333"
    # Qdrant Cloud API key (optional — leave empty for local/unauthenticated Qdrant)
    qdrant_api_key: str = ""

    # Langfuse tracing (optional)
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_base_url: str = "https://cloud.langfuse.com"

    # Auth (Supabase)
    supabase_url: str = ""
    supabase_jwt_secret: str = ""

    # Billing (Polar.sh)
    polar_webhook_secret: str = ""
    polar_pro_product_id: str = ""
    polar_ultra_product_id: str = ""

    # Auth toggle (set False for local dev / tests)
    auth_enabled: bool = True

    # CORS origins (comma-separated in env, parsed below)
    cors_origins: str = "https://app.cherryevals.com,http://localhost:5173"

    # Optional overrides
    cherry_data_dir: Path = Path("./data")
    cherry_log_level: str = "INFO"

    @model_validator(mode="after")
    def _check_auth_secrets(self) -> "Settings":
        """Disable auth if JWT secret is missing (safe dev default).

        In production, SUPABASE_JWT_SECRET must be set when AUTH_ENABLED=True.
        Locally this falls back to open access with a loud warning.
        """
        if self.auth_enabled and not self.supabase_jwt_secret:
            _config_logger.warning(
                "AUTH_ENABLED=True but SUPABASE_JWT_SECRET is empty — "
                "falling back to AUTH_ENABLED=False. "
                "Set SUPABASE_JWT_SECRET for production."
            )
            self.auth_enabled = False
        return self


settings = Settings()
