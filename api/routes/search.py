"""Search API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.models.search import SearchRequest, SearchResponse, SearchResultItem
from core.search.keyword import keyword_search
from db.postgres.base import get_db

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
