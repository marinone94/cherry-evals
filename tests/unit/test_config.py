"""Unit tests for configuration."""

from pathlib import Path

from cherry_evals.config import Settings


def test_settings_default_values(monkeypatch, tmp_path):
    """Test that Settings has correct default values when no env is set."""
    # Prevent reading .env file by changing to a temp dir with no .env
    monkeypatch.chdir(tmp_path)
    # Clear any env vars that would override defaults
    for var in [
        "GOOGLE_API_KEY",
        "GOOGLE_GENAI_USE_VERTEXAI",
        "ANTHROPIC_API_KEY",
        "CEREBRAS_API_KEY",
        "DATABASE_URL",
        "QDRANT_URL",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_BASE_URL",
        "CHERRY_DATA_DIR",
        "CHERRY_LOG_LEVEL",
    ]:
        monkeypatch.delenv(var, raising=False)

    settings = Settings()

    assert settings.google_api_key == ""
    assert settings.google_genai_use_vertexai == 0
    assert settings.anthropic_api_key == ""
    assert settings.cerebras_api_key == ""
    assert settings.database_url == "postgresql://cherry:cherry@localhost:5433/cherry_evals"
    assert settings.qdrant_url == "http://localhost:6333"
    assert settings.langfuse_base_url == "https://cloud.langfuse.com"
    assert settings.cherry_data_dir == Path("./data")
    assert settings.cherry_log_level == "INFO"


def test_settings_env_override(monkeypatch):
    """Test that environment variables override default values."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-123")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@testhost:5432/testdb")
    monkeypatch.setenv("QDRANT_URL", "http://testhost:6333")
    monkeypatch.setenv("CHERRY_LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.google_api_key == "test-key-123"
    assert settings.database_url == "postgresql://test:test@testhost:5432/testdb"
    assert settings.qdrant_url == "http://testhost:6333"
    assert settings.cherry_log_level == "DEBUG"


def test_settings_path_type():
    """Test that cherry_data_dir is a Path object."""
    settings = Settings()

    assert isinstance(settings.cherry_data_dir, Path)


def test_settings_case_insensitive(monkeypatch):
    """Test that environment variables are case-insensitive."""
    monkeypatch.setenv("cherry_log_level", "WARNING")

    settings = Settings()

    assert settings.cherry_log_level == "WARNING"


def test_settings_extra_fields_ignored(monkeypatch):
    """Test that extra environment variables are ignored."""
    monkeypatch.setenv("RANDOM_ENV_VAR", "should-be-ignored")

    # Should not raise an error
    settings = Settings()

    assert not hasattr(settings, "random_env_var")
