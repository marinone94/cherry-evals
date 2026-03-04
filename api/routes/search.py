"""Search API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.models.search import (
    HybridSearchRequest,
    IntelligentSearchRequest,
    IntelligentSearchResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SemanticSearchRequest,
)
from core.search.keyword import keyword_search
from db.postgres.base import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(request: SearchRequest, db: Session = Depends(get_db)):
    """Search examples by keyword.

    Searches across question and answer text using pattern matching.
    Supports filtering by dataset and subject.
    """
    results, total = keyword_search(
        db=db,
        query=request.query,
        dataset_name=request.dataset,
        subject=request.subject,
        limit=request.limit,
        offset=request.offset,
    )

    return SearchResponse(
        results=[SearchResultItem(**r) for r in results],
        total=total,
        query=request.query,
        offset=request.offset,
        limit=request.limit,
    )


@router.post("/semantic", response_model=SearchResponse)
def search_semantic(request: SemanticSearchRequest):
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
        logger.warning(f"Semantic search failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Semantic search unavailable: {e}",
        )

    return SearchResponse(
        results=[SearchResultItem(**r) for r in results],
        total=len(results),
        query=request.query,
        offset=0,
        limit=request.limit,
    )


@router.post("/hybrid", response_model=SearchResponse)
def search_hybrid(request: HybridSearchRequest, db: Session = Depends(get_db)):
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
            limit=request.limit,
            offset=request.offset,
            keyword_weight=request.keyword_weight,
            semantic_weight=request.semantic_weight,
            collection_name=request.collection,
        )
    except Exception as e:
        # Fall back to keyword search if semantic/hybrid fails
        logger.warning(f"Hybrid search failed, falling back to keyword: {e}")
        kw_results, total = keyword_search(
            db=db,
            query=request.query,
            dataset_name=request.dataset,
            subject=request.subject,
            limit=request.limit,
            offset=request.offset,
        )
        results = kw_results

    return SearchResponse(
        results=[SearchResultItem(**r) for r in results],
        total=total,
        query=request.query,
        offset=request.offset,
        limit=request.limit,
    )


@router.post("/intelligent", response_model=IntelligentSearchResponse)
def search_intelligent(request: IntelligentSearchRequest, db: Session = Depends(get_db)):
    """LLM-powered intelligent search with query understanding and result re-ranking.

    Uses Gemini Flash to parse the natural language query into structured
    parameters (expanded query, dataset filter, subject filter), runs hybrid
    search, and re-ranks results for relevance and diversity.

    Falls back gracefully if LLM calls or semantic search are unavailable.
    """
    from core.search.intelligent import intelligent_search

    results, total, metadata = intelligent_search(
        db=db,
        query=request.query,
        limit=request.limit,
        offset=request.offset,
    )

    return IntelligentSearchResponse(
        results=[SearchResultItem(**r) for r in results],
        total=total,
        query=request.query,
        offset=request.offset,
        limit=request.limit,
        metadata=metadata,
    )
