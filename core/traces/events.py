"""Event tracking service for curation traces."""

import logging
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.postgres.models import CurationEvent

logger = logging.getLogger(__name__)

_SESSION_ID_RE = re.compile(r"^[0-9a-zA-Z\-_]{1,100}$")


def record_event(
    db: Session,
    event_type: str,
    session_id: str | None = None,
    user_id: str | None = None,
    example_id: int | None = None,
    collection_id: int | None = None,
    dataset_id: int | None = None,
    query: str | None = None,
    search_mode: str | None = None,
    result_position: int | None = None,
    result_score: float | None = None,
    export_format: str | None = None,
    metadata: dict | None = None,
) -> CurationEvent | None:
    """Record a curation event. Non-blocking — failures are logged, not raised."""
    # Validate session_id format to prevent arbitrary string storage
    if session_id and not _SESSION_ID_RE.match(session_id):
        session_id = None
    try:
        event = CurationEvent(
            event_type=event_type,
            session_id=session_id,
            user_id=user_id,
            example_id=example_id,
            collection_id=collection_id,
            dataset_id=dataset_id,
            query=query,
            search_mode=search_mode,
            result_position=result_position,
            result_score=result_score,
            export_format=export_format,
            event_metadata=metadata,
        )
        db.add(event)
        db.flush()
        return event
    except Exception:
        logger.exception("Failed to record curation event (event_type=%s)", event_type)
        return None


def get_event_stats(db: Session, user_id: str | None = None) -> dict:
    """Get aggregate stats on curation events.

    When *user_id* is provided, all queries are scoped to that user.
    When anonymous (user_id=None), raw query strings are omitted for privacy.

    Returns a dict with total_events, events_by_type, most_searched_queries, etc.
    """
    base_filter = (CurationEvent.user_id == user_id,) if user_id else ()

    total_events = (
        db.execute(select(func.count(CurationEvent.id)).where(*base_filter)).scalar() or 0
    )

    # Events grouped by type
    rows = db.execute(
        select(CurationEvent.event_type, func.count(CurationEvent.id).label("cnt"))
        .where(*base_filter)
        .group_by(CurationEvent.event_type)
        .order_by(func.count(CurationEvent.id).desc())
    ).all()
    events_by_type = {row.event_type: row.cnt for row in rows}

    # Most searched queries (top 10) — only shown to authenticated users
    most_searched_queries: list[dict] = []
    if user_id:
        query_rows = db.execute(
            select(CurationEvent.query, func.count(CurationEvent.id).label("cnt"))
            .where(
                CurationEvent.event_type == "search",
                CurationEvent.query.isnot(None),
                *base_filter,
            )
            .group_by(CurationEvent.query)
            .order_by(func.count(CurationEvent.id).desc())
            .limit(10)
        ).all()
        most_searched_queries = [{"query": r.query, "count": r.cnt} for r in query_rows]

    # Most picked examples (top 10)
    pick_rows = db.execute(
        select(CurationEvent.example_id, func.count(CurationEvent.id).label("cnt"))
        .where(
            CurationEvent.event_type == "pick",
            CurationEvent.example_id.isnot(None),
            *base_filter,
        )
        .group_by(CurationEvent.example_id)
        .order_by(func.count(CurationEvent.id).desc())
        .limit(10)
    ).all()
    most_picked_examples = [{"example_id": r.example_id, "pick_count": r.cnt} for r in pick_rows]

    return {
        "total_events": total_events,
        "events_by_type": events_by_type,
        "most_searched_queries": most_searched_queries,
        "most_picked_examples": most_picked_examples,
    }


def get_example_pick_count(db: Session, example_id: int) -> int:
    """How many times an example has been picked across all collections."""
    count = db.execute(
        select(func.count(CurationEvent.id)).where(
            CurationEvent.event_type == "pick",
            CurationEvent.example_id == example_id,
        )
    ).scalar()
    return count or 0


def get_popular_examples(db: Session, limit: int = 20) -> list[dict]:
    """Most frequently picked examples across all users."""
    rows = db.execute(
        select(CurationEvent.example_id, func.count(CurationEvent.id).label("pick_count"))
        .where(CurationEvent.event_type == "pick", CurationEvent.example_id.isnot(None))
        .group_by(CurationEvent.example_id)
        .order_by(func.count(CurationEvent.id).desc())
        .limit(limit)
    ).all()
    return [{"example_id": r.example_id, "pick_count": r.pick_count} for r in rows]


def get_co_picked_examples(db: Session, example_id: int, limit: int = 10) -> list[dict]:
    """Examples commonly picked alongside a given example.

    Finds all collections that contain the given example, then counts how
    often other examples appear in those same collections (via pick events).
    """
    # Find all collection_ids where the given example was picked
    collection_ids = (
        db.execute(
            select(CurationEvent.collection_id)
            .where(
                CurationEvent.event_type == "pick",
                CurationEvent.example_id == example_id,
                CurationEvent.collection_id.isnot(None),
            )
            .distinct()
        )
        .scalars()
        .all()
    )

    if not collection_ids:
        return []

    # Count other examples picked in those same collections
    rows = db.execute(
        select(CurationEvent.example_id, func.count(CurationEvent.id).label("co_pick_count"))
        .where(
            CurationEvent.event_type == "pick",
            CurationEvent.collection_id.in_(collection_ids),
            CurationEvent.example_id.isnot(None),
            CurationEvent.example_id != example_id,
        )
        .group_by(CurationEvent.example_id)
        .order_by(func.count(CurationEvent.id).desc())
        .limit(limit)
    ).all()

    return [{"example_id": r.example_id, "co_pick_count": r.co_pick_count} for r in rows]
