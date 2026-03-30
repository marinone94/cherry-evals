"""Analytics API endpoints for curation event insights."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_optional_user
from core.traces.events import get_co_picked_examples, get_event_stats, get_popular_examples
from db.postgres.base import get_db
from db.postgres.models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/stats")
def analytics_stats(
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Return curation event stats, scoped to the authenticated user when present.

    Authenticated users see their own stats including query history.
    Unauthenticated requests see aggregate counts only (queries omitted for privacy).
    """
    user_id = user.supabase_id if user else None
    return get_event_stats(db=db, user_id=user_id)


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
