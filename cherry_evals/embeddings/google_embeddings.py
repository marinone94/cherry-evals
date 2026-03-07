"""Google GenAI embedding provider."""

from google import genai

from cherry_evals.config import settings

# Google embedding model specs
_MODEL_DIMENSIONS = {
    "text-embedding-005": 768,
}

_DEFAULT_MODEL = "text-embedding-005"


class GoogleEmbeddingProvider:
    """Embedding provider using Google GenAI API."""

    def __init__(self, model: str = _DEFAULT_MODEL) -> None:
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY not set in environment")
        if model not in _MODEL_DIMENSIONS:
            raise ValueError(f"Unknown model: {model}. Available: {list(_MODEL_DIMENSIONS.keys())}")

        self._model = model
        self._dimensions = _MODEL_DIMENSIONS[model]
        self._client = genai.Client(api_key=settings.google_api_key)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts using Google GenAI.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (list of floats).
        """
        result = self._client.models.embed_content(
            model=self._model,
            contents=texts,
        )
        return [embedding.values for embedding in result.embeddings]

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model
