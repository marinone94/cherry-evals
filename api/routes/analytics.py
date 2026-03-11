"""Analytics API endpoints for curation event insights."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.traces.events import get_co_picked_examples, get_event_stats, get_popular_examples
from db.postgres.base import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/stats")
def analytics_stats(db: Session = Depends(get_db)):
    """Return overall curation event stats.

    Includes total events, events by type, most searched queries,
    and most picked examples.
    """
    return get_event_stats(db=db)


@router.get("/popular")
def analytics_popular(
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return the most frequently picked examples across all users."""
    return get_popular_examples(db=db, limit=limit)


@router.get("/co-picked/{example_id}")
def analytics_co_picked(
    example_id: int,
    limit: int = Query(10, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return examples commonly picked alongside the given example."""
    return get_co_picked_examples(db=db, example_id=example_id, limit=limit)
