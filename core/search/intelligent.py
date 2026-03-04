"""Intelligent search orchestrator combining query understanding and result re-ranking.

Flow:
  1. Parse the natural language query with the query agent (Gemini Flash).
  2. Determine which Qdrant collection to search (from detected dataset or caller).
  3. Run hybrid search using the expanded query and detected filters.
  4. Re-rank results with the re-ranker agent (Gemini Flash).
  5. Return results + metadata about the LLM reasoning.
"""

import logging

from sqlalchemy.orm import Session

from agents.query_agent import parse_query
from agents.reranker import rerank_results
from core.search.hybrid import hybrid_search
from core.search.keyword import keyword_search

logger = logging.getLogger(__name__)

# Map canonical dataset names to their Qdrant collection names
_DATASET_COLLECTION_MAP = {
    "MMLU": "mmlu_embeddings",
    "HumanEval": "humaneval_embeddings",
    "GSM8K": "gsm8k_embeddings",
    "HellaSwag": "hellaswag_embeddings",
    "TruthfulQA": "truthfulqa_embeddings",
    "ARC": "arc_embeddings",
}

_DEFAULT_COLLECTION = "mmlu_embeddings"


def _resolve_collection(dataset: str | None, collection_name: str | None) -> str:
    """Determine which Qdrant collection to search.

    Caller-supplied collection takes priority. If a dataset was detected by
    the query agent, map it to the corresponding collection. Otherwise fall
    back to the default collection.
    """
    if collection_name:
        return collection_name
    if dataset and dataset in _DATASET_COLLECTION_MAP:
        return _DATASET_COLLECTION_MAP[dataset]
    return _DEFAULT_COLLECTION


def intelligent_search(
    db: Session,
    query: str,
    limit: int = 20,
    offset: int = 0,
    collection_name: str | None = None,
) -> tuple[list[dict], int, dict]:
    """LLM-powered intelligent search over evaluation datasets.

    Uses Gemini Flash to understand the query intent, runs hybrid search with
    the expanded query and extracted filters, then re-ranks results for
    relevance and diversity.

    Falls back to keyword-only search if semantic / hybrid search fails.
    LLM failures are handled gracefully — query understanding and re-ranking
    are best-effort enhancements that do not block search.

    Args:
        db: SQLAlchemy database session.
        query: Raw natural language query from the user.
        limit: Maximum number of results to return.
        offset: Pagination offset.
        collection_name: Optional Qdrant collection to search. If None, the
                         collection is derived from the detected dataset.

    Returns:
        Tuple of (results, total, metadata) where:
            - results is the paginated, re-ranked list of result dicts
            - total is the total number of results before pagination
            - metadata is a dict with query understanding and re-ranking info
    """
    # Step 1: Understand the query
    parsed = parse_query(query)
    logger.info(
        "Query understanding: search_query=%r dataset=%r subject=%r task_type=%r",
        parsed["search_query"],
        parsed["dataset"],
        parsed["subject"],
        parsed["task_type"],
    )

    # Step 2: Resolve collection
    collection = _resolve_collection(parsed["dataset"], collection_name)

    # Step 3: Hybrid search (with fallback to keyword)
    fetch_limit = min(limit + offset + 30, 200)
    try:
        raw_results, raw_total = hybrid_search(
            db=db,
            query=parsed["search_query"],
            dataset_name=parsed["dataset"],
            subject=parsed["subject"],
            limit=fetch_limit,
            offset=0,
            collection_name=collection,
        )
    except Exception as exc:
        logger.warning("Hybrid search failed, falling back to keyword only: %s", exc)
        raw_results, raw_total = keyword_search(
            db=db,
            query=parsed["search_query"],
            dataset_name=parsed["dataset"],
            subject=parsed["subject"],
            limit=fetch_limit,
            offset=0,
        )

    # Step 4: Re-rank results
    reranked = rerank_results(
        query=parsed["search_query"],
        results=raw_results,
        limit=len(raw_results),  # Re-rank all; pagination applied after
    )

    # Step 5: Apply pagination and build response
    total = len(reranked)
    paginated = reranked[offset : offset + limit]

    metadata = {
        "original_query": query,
        "parsed": {
            "search_query": parsed["search_query"],
            "dataset": parsed["dataset"],
            "subject": parsed["subject"],
            "task_type": parsed["task_type"],
            "explanation": parsed["explanation"],
        },
        "collection_searched": collection,
        "reranking_applied": True,
    }

    return paginated, total, metadata
