"""Qdrant client for vector storage."""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from cherry_evals.config import settings


def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client instance.

    Connects with API key when ``QDRANT_API_KEY`` is set (Qdrant Cloud),
    otherwise connects without authentication (local / self-hosted).
    """
    kwargs: dict = {"url": settings.qdrant_url, "timeout": 60}
    if settings.qdrant_api_key:
        kwargs["api_key"] = settings.qdrant_api_key
    return QdrantClient(**kwargs)


def create_collection(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
    distance: Distance = Distance.COSINE,
) -> None:
    """Create a collection in Qdrant if it doesn't exist.

    Args:
        client: Qdrant client instance
        collection_name: Name of the collection
        vector_size: Dimension of the vectors
        distance: Distance metric (COSINE, EUCLID, DOT)
    """
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=distance),
        )
        print(f"Created Qdrant collection: {collection_name}")
    else:
        print(f"Qdrant collection already exists: {collection_name}")


def upsert_vectors(
    client: QdrantClient,
    collection_name: str,
    points: list[PointStruct],
) -> None:
    """Upsert vectors into a Qdrant collection.

    Args:
        client: Qdrant client instance
        collection_name: Name of the collection
        points: List of PointStruct objects containing id, vector, and payload
    """
    client.upsert(collection_name=collection_name, points=points)
