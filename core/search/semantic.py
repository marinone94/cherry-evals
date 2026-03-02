"""Semantic search using Qdrant vector similarity."""

from cherry_evals.embeddings.google_embeddings import GoogleEmbeddingProvider
from db.qdrant.client import get_qdrant_client


def semantic_search(
    query: str,
    collection_name: str = "mmlu_embeddings",
    limit: int = 20,
    score_threshold: float | None = None,
    subject: str | None = None,
) -> list[dict]:
    """Search examples by vector similarity in Qdrant.

    Args:
        query: Natural language search query
        collection_name: Qdrant collection to search
        limit: Max results to return
        score_threshold: Min similarity score (0-1)
        subject: Optional filter by subject in payload

    Returns:
        List of result dicts with score, ordered by relevance
    """
    # Embed the query
    provider = GoogleEmbeddingProvider()
    query_vector = provider.embed_batch([query])[0]

    client = get_qdrant_client()

    # Build Qdrant filter if needed
    query_filter = None
    if subject is not None:
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        query_filter = Filter(must=[FieldCondition(key="subject", match=MatchValue(value=subject))])

    search_results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        query_filter=query_filter,
        limit=limit,
        score_threshold=score_threshold,
        with_payload=True,
    ).points

    results = []
    for point in search_results:
        payload = point.payload or {}
        results.append(
            {
                "id": payload.get("example_id", point.id),
                "dataset_id": payload.get("dataset_id"),
                "dataset_name": payload.get("dataset_name", ""),
                "question": payload.get("question", ""),
                "answer": None,
                "choices": None,
                "example_metadata": {
                    "subject": payload.get("subject"),
                    "split": payload.get("split"),
                },
                "score": point.score,
            }
        )

    return results
