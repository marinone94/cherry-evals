"""Configuration for Cherry Evals using pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Optional overrides
    cherry_data_dir: Path = Path("./data")
    cherry_log_level: str = "INFO"


settings = Settings()
