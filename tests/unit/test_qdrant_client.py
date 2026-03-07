"""Unit tests for the Qdrant client factory."""

from unittest.mock import MagicMock, patch

from db.qdrant.client import get_qdrant_client


def test_get_qdrant_client_no_api_key(monkeypatch):
    """Without an API key, the client is created with only the URL (local mode)."""
    monkeypatch.setattr("db.qdrant.client.settings.qdrant_url", "http://localhost:6333")
    monkeypatch.setattr("db.qdrant.client.settings.qdrant_api_key", "")

    with patch("db.qdrant.client.QdrantClient") as mock_client_cls:
        mock_client_cls.return_value = MagicMock()
        get_qdrant_client()

    mock_client_cls.assert_called_once_with(url="http://localhost:6333")


def test_get_qdrant_client_with_api_key(monkeypatch):
    """With an API key set, the client is created with both URL and api_key (cloud mode)."""
    monkeypatch.setattr("db.qdrant.client.settings.qdrant_url", "https://xyz.qdrant.io:6333")
    monkeypatch.setattr("db.qdrant.client.settings.qdrant_api_key", "secret-cloud-key")

    with patch("db.qdrant.client.QdrantClient") as mock_client_cls:
        mock_client_cls.return_value = MagicMock()
        get_qdrant_client()

    mock_client_cls.assert_called_once_with(
        url="https://xyz.qdrant.io:6333",
        api_key="secret-cloud-key",
    )


def test_get_qdrant_client_returns_client_instance(monkeypatch):
    """get_qdrant_client returns the QdrantClient instance."""
    monkeypatch.setattr("db.qdrant.client.settings.qdrant_url", "http://localhost:6333")
    monkeypatch.setattr("db.qdrant.client.settings.qdrant_api_key", "")

    fake_client = MagicMock()
    with patch("db.qdrant.client.QdrantClient", return_value=fake_client):
        client = get_qdrant_client()

    assert client is fake_client
