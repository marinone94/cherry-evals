"""Embedding provider interface and registry."""

from typing import Protocol


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers.

    Any embedding provider must implement embed_batch, dimensions, and model_name.
    """

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        ...

    @property
    def dimensions(self) -> int:
        """Vector dimensionality of this provider's embeddings."""
        ...

    @property
    def model_name(self) -> str:
        """Model identifier string."""
        ...
