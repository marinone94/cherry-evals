"""Unit tests for the Google embedding provider."""

from unittest.mock import MagicMock, patch

import pytest

from cherry_evals.embeddings.google_embeddings import (
    _DEFAULT_MODEL,
    _MODEL_DIMENSIONS,
    GoogleEmbeddingProvider,
)


def test_default_model_is_text_embedding_005():
    """Default embedding model must be gemini-embedding-001."""
    assert _DEFAULT_MODEL == "gemini-embedding-001"


def test_model_dimensions_contains_005():
    """gemini-embedding-001 must be registered with 3072 dimensions."""
    assert "gemini-embedding-001" in _MODEL_DIMENSIONS
    assert _MODEL_DIMENSIONS["gemini-embedding-001"] == 3072


def test_model_dimensions_does_not_contain_004():
    """Discontinued text-embedding-004 must not be in the model registry."""
    assert "text-embedding-004" not in _MODEL_DIMENSIONS


def test_provider_raises_without_api_key(monkeypatch):
    """GoogleEmbeddingProvider raises ValueError when GOOGLE_API_KEY is not set."""
    monkeypatch.setattr(
        "cherry_evals.embeddings.google_embeddings.settings",
        MagicMock(google_api_key=""),
    )
    with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
        GoogleEmbeddingProvider()


def test_provider_raises_for_unknown_model(monkeypatch):
    """GoogleEmbeddingProvider raises ValueError for an unrecognised model."""
    monkeypatch.setattr(
        "cherry_evals.embeddings.google_embeddings.settings",
        MagicMock(google_api_key="key"),
    )
    with patch("cherry_evals.embeddings.google_embeddings.genai"):
        with pytest.raises(ValueError, match="Unknown model"):
            GoogleEmbeddingProvider(model="text-embedding-004")


def test_provider_dimensions_and_model_name(monkeypatch):
    """GoogleEmbeddingProvider exposes correct dimensions and model_name."""
    monkeypatch.setattr(
        "cherry_evals.embeddings.google_embeddings.settings",
        MagicMock(google_api_key="key"),
    )
    with patch("cherry_evals.embeddings.google_embeddings.genai"):
        provider = GoogleEmbeddingProvider(model="gemini-embedding-001")

    assert provider.dimensions == 3072
    assert provider.model_name == "gemini-embedding-001"
