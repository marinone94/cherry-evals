"""Search API endpoints."""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from api.deps import (
    check_and_increment_llm_budget,
    check_search_rate_limit,
    check_semantic_search_quota,
    require_paid,
)
from api.models.search import (
    FacetRequest,
    FacetResponse,
    HybridSearchRequest,
    IntelligentSearchRequest,
    IntelligentSearchResponse,
    SearchIterationModel,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SemanticSearchRequest,
)
from core.search.keyword import keyword_search
from core.traces.events import record_event
from db.postgres.base import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post(
    "",
    response_model=SearchResponse,
    dependencies=[Depends(check_search_rate_limit)],
)
def search(
    request: SearchRequest,
    db: Session = Depends(get_db),
    x_session_id: str | None = Header(default=None),
):
    """Search examples by keyword.

    Searches across question and answer text using pattern matching.
    Supports filtering by dataset, subject, and task_type, and sort options.
    """
    results, total = keyword_search(
        db=db,
        query=request.query,
        dataset_name=request.dataset,
        subject=request.subject,
        task_type=request.task_type,
        limit=request.limit,
        offset=request.offset,
        sort_by=request.sort_by,
    )

    try:
        record_event(
            db=db,
            event_type="search",
            session_id=x_session_id,
            query=request.query,
            search_mode="keyword",
        )
    except Exception:
        logger.exception("Failed to record search event")

    return SearchResponse(
        results=[SearchResultItem(**r) for r in results],
        total=total,
        query=request.query,
        offset=request.offset,
        limit=request.limit,
    )


@router.post(
    "/semantic",
    response_model=SearchResponse,
    dependencies=[Depends(check_semantic_search_quota)],
)
def search_semantic(
    request: SemanticSearchRequest,
    x_session_id: str | None = Header(default=None),
):
    """Search examples by semantic similarity.

    Embeds the query and finds nearest neighbors in the vector database.
    Requires embeddings to be generated for the target collection.
    """
    from core.search.semantic import semantic_search

    try:
        results = semantic_search(
            query=request.query,
            collection_name=request.collection,
            limit=request.limit,
            score_threshold=request.score_threshold,
            subject=request.subject,
        )
    except Exception as e:
        logger.warning("Semantic search failed: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Semantic search is temporarily unavailable.",
        )

    return SearchResponse(
        results=[SearchResultItem(**r) for r in results],
        total=len(results),
        query=request.query,
        offset=0,
        limit=request.limit,
    )


@router.post("/hybrid", response_model=SearchResponse)
def search_hybrid(
    request: HybridSearchRequest,
    db: Session = Depends(get_db),
    x_session_id: str | None = Header(default=None),
):
    """Combined keyword + semantic search.

    Runs both searches and merges results using Reciprocal Rank Fusion (RRF).
    Falls back to keyword-only if semantic search is unavailable.
    """
    from core.search.hybrid import hybrid_search

    try:
        results, total = hybrid_search(
            db=db,
            query=request.query,
            dataset_name=request.dataset,
            subject=request.subject,
            task_type=request.task_type,
            limit=request.limit,
            offset=request.offset,
            keyword_weight=request.keyword_weight,
            semantic_weight=request.semantic_weight,
            collection_name=request.collection,
        )
    except Exception as e:
        # Fall back to keyword search if semantic/hybrid fails
        logger.warning("Hybrid search failed, falling back to keyword: %s", e)
        kw_results, total = keyword_search(
            db=db,
            query=request.query,
            dataset_name=request.dataset,
            subject=request.subject,
            task_type=request.task_type,
            limit=request.limit,
            offset=request.offset,
        )
        results = kw_results

    try:
        record_event(
            db=db,
            event_type="search",
            session_id=x_session_id,
            query=request.query,
            search_mode="hybrid",
        )
    except Exception:
        logger.exception("Failed to record hybrid search event")

    return SearchResponse(
        results=[SearchResultItem(**r) for r in results],
        total=total,
        query=request.query,
        offset=request.offset,
        limit=request.limit,
    )


@router.post(
    "/intelligent",
    response_model=IntelligentSearchResponse,
    dependencies=[Depends(require_paid), Depends(check_and_increment_llm_budget)],
)
def search_intelligent(
    request: IntelligentSearchRequest,
    db: Session = Depends(get_db),
    x_session_id: str | None = Header(default=None),
):
    """LLM-powered intelligent search with query understanding and result re-ranking.

    Supports two strategies:
    - ``agent`` (default): An autonomous search agent that iterates, evaluates
      results, and refines the query up to ``max_iterations`` times. Returns
      a full trace of agent iterations.
    - ``pipeline``: Fixed DAG — parse → hybrid search → rerank.  The original
      behaviour, kept for backward compatibility.

    Falls back gracefully if LLM calls or semantic search are unavailable.
    """
    strategy = (request.strategy or "agent").lower()

    if strategy == "agent":
        from agents.search_agent import SearchAgent

        agent = SearchAgent(db=db, max_iterations=request.max_iterations)
        agent_result = agent.search(query=request.query, limit=request.limit)

        # Apply pagination offset after agent returns results
        paginated = agent_result.results[request.offset : request.offset + request.limit]

        iterations_out = [
            SearchIterationModel(
                tool_used=it.tool_used,
                query=it.query,
                filters=it.filters,
                result_count=it.result_count,
                evaluation=it.evaluation,
            )
            for it in agent_result.iterations
        ]

        try:
            record_event(
                db=db,
                event_type="search",
                session_id=x_session_id,
                query=request.query,
                search_mode="intelligent_agent",
            )
        except Exception:
            logger.exception("Failed to record intelligent agent search event")

        return IntelligentSearchResponse(
            results=[SearchResultItem(**r) for r in paginated],
            total=agent_result.total,
            query=request.query,
            offset=request.offset,
            limit=request.limit,
            metadata={"query_understanding": agent_result.query_understanding},
            iterations=iterations_out,
            final_evaluation=agent_result.final_evaluation,
            query_understanding=agent_result.query_understanding,
            strategy_used="agent",
        )

    # strategy == "pipeline" — original fixed DAG
    from core.search.intelligent import intelligent_search

    results, total, metadata = intelligent_search(
        db=db,
        query=request.query,
        limit=request.limit,
        offset=request.offset,
    )

    try:
        record_event(
            db=db,
            event_type="search",
            session_id=x_session_id,
            query=request.query,
            search_mode="intelligent",
        )
    except Exception:
        logger.exception("Failed to record intelligent search event")

    return IntelligentSearchResponse(
        results=[SearchResultItem(**r) for r in results],
        total=total,
        query=request.query,
        offset=request.offset,
        limit=request.limit,
        metadata=metadata,
        strategy_used="pipeline",
    )


@router.post("/facets", response_model=FacetResponse)
def get_facets(request: FacetRequest, db: Session = Depends(get_db)):
    """Return facet counts grouped by dataset, subject, and task_type.

    When *query* is provided the counts mirror what keyword search would return.
    When *query* is None (or omitted) counts cover all examples.
    """
    from core.search.facets import get_facets as _get_facets

    facets = _get_facets(db=db, query=request.query)
    return FacetResponse(**facets)
