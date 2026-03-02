"""Hybrid search combining keyword and semantic results.

Uses Reciprocal Rank Fusion (RRF) to merge results from both sources.
"""

from sqlalchemy.orm import Session

from core.search.keyword import keyword_search
from core.search.semantic import semantic_search


def _reciprocal_rank_fusion(
    keyword_results: list[dict],
    semantic_results: list[dict],
    keyword_weight: float = 0.4,
    semantic_weight: float = 0.6,
    k: int = 60,
) -> list[dict]:
    """Merge two result lists using Reciprocal Rank Fusion.

    RRF score for each document = sum of (weight / (k + rank)) across all lists
    where it appears. k is a constant (typically 60) that prevents high-ranked
    items from dominating.

    Args:
        keyword_results: Results from keyword search
        semantic_results: Results from semantic search
        keyword_weight: Weight for keyword results
        semantic_weight: Weight for semantic results
        k: RRF constant

    Returns:
        Merged, deduplicated results sorted by fused score
    """
    scores: dict[int, float] = {}
    result_map: dict[int, dict] = {}

    # Score keyword results
    for rank, result in enumerate(keyword_results):
        example_id = result["id"]
        scores[example_id] = scores.get(example_id, 0) + keyword_weight / (k + rank + 1)
        result_map[example_id] = result

    # Score semantic results
    for rank, result in enumerate(semantic_results):
        example_id = result["id"]
        scores[example_id] = scores.get(example_id, 0) + semantic_weight / (k + rank + 1)
        # Semantic results may have less detail; prefer keyword version if available
        if example_id not in result_map:
            result_map[example_id] = result

    # Sort by fused score descending
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    fused_results = []
    for example_id in sorted_ids:
        result = result_map[example_id].copy()
        result["score"] = scores[example_id]
        fused_results.append(result)

    return fused_results


def hybrid_search(
    db: Session,
    query: str,
    dataset_name: str | None = None,
    subject: str | None = None,
    limit: int = 20,
    offset: int = 0,
    keyword_weight: float = 0.4,
    semantic_weight: float = 0.6,
    collection_name: str = "mmlu_embeddings",
) -> tuple[list[dict], int]:
    """Combined keyword + semantic search with RRF fusion.

    Runs both searches, fuses results, and returns paginated output.

    Args:
        db: Database session for keyword search
        query: Search query string
        dataset_name: Optional filter by dataset name
        subject: Optional filter by subject
        limit: Max results to return
        offset: Pagination offset
        keyword_weight: Weight for keyword results (0-1)
        semantic_weight: Weight for semantic results (0-1)
        collection_name: Qdrant collection for semantic search

    Returns:
        Tuple of (paginated results, total fused count)
    """
    # Fetch more results than needed from each source for better fusion
    fetch_limit = min(limit + offset + 50, 200)

    # Run keyword search
    keyword_results, _ = keyword_search(
        db=db,
        query=query,
        dataset_name=dataset_name,
        subject=subject,
        limit=fetch_limit,
        offset=0,
    )

    # Run semantic search
    semantic_results = semantic_search(
        query=query,
        collection_name=collection_name,
        limit=fetch_limit,
        subject=subject,
    )

    # Fuse results
    fused = _reciprocal_rank_fusion(
        keyword_results=keyword_results,
        semantic_results=semantic_results,
        keyword_weight=keyword_weight,
        semantic_weight=semantic_weight,
    )

    total = len(fused)

    # Apply pagination
    paginated = fused[offset : offset + limit]

    return paginated, total
