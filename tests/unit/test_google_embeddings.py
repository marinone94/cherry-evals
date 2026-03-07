"""Unit tests for the Google embedding provider."""

from unittest.mock import MagicMock, patch

import pytest

from cherry_evals.embeddings.google_embeddings import (
    _DEFAULT_MODEL,
    _MODEL_DIMENSIONS,
    GoogleEmbeddingProvider,
)


def test_default_model_is_text_embedding_005():
    """Default embedding model must be text-embedding-005."""
    assert _DEFAULT_MODEL == "text-embedding-005"


def test_model_dimensions_contains_005():
    """text-embedding-005 must be registered with 768 dimensions."""
    assert "text-embedding-005" in _MODEL_DIMENSIONS
    assert _MODEL_DIMENSIONS["text-embedding-005"] == 768


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
        provider = GoogleEmbeddingProvider(model="text-embedding-005")

    assert provider.dimensions == 768
    assert provider.model_name == "text-embedding-005"
