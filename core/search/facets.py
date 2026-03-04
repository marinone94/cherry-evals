"""Faceted search: counts by dataset, subject, and task_type.

Uses GROUP BY queries against Postgres so the caller can populate
filter dropdowns without running a full search first.
"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.postgres.models import Dataset, Example


def get_facets(
    db: Session,
    query: str | None = None,
) -> dict[str, Any]:
    """Return counts grouped by dataset, subject, and task_type.

    When *query* is provided the counts reflect only examples whose
    question or answer ILIKE the query pattern, matching the behaviour
    of keyword_search.  When *query* is None all examples are counted.

    Args:
        db: Database session.
        query: Optional keyword to filter examples before counting.

    Returns:
        Dict with keys ``datasets``, ``subjects``, ``task_types``, ``total``.
    """

    # Build the base join once; all facet queries share the same filter.
    def _apply_filter(stmt, query: str | None):
        if query:
            from sqlalchemy import or_

            pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Example.question.ilike(pattern),
                    Example.answer.ilike(pattern),
                )
            )
        return stmt

    # ── Dataset facet ────────────────────────────────────────────────────────
    ds_stmt = _apply_filter(
        select(Dataset.name, func.count(Example.id).label("count"))
        .join(Dataset, Example.dataset_id == Dataset.id)
        .group_by(Dataset.name)
        .order_by(Dataset.name),
        query,
    )
    datasets = [{"name": row.name, "count": row.count} for row in db.execute(ds_stmt).all()]

    # ── Subject facet ────────────────────────────────────────────────────────
    # subject lives in example_metadata JSON; we skip rows where it is NULL.
    subj_stmt = _apply_filter(
        select(
            Example.example_metadata["subject"].as_string().label("subject"),
            Dataset.name.label("dataset"),
            func.count(Example.id).label("count"),
        )
        .join(Dataset, Example.dataset_id == Dataset.id)
        .where(Example.example_metadata["subject"].as_string() != None)  # noqa: E711
        .group_by(
            Example.example_metadata["subject"].as_string(),
            Dataset.name,
        )
        .order_by(Dataset.name, Example.example_metadata["subject"].as_string()),
        query,
    )
    subjects = [
        {"name": row.subject, "dataset": row.dataset, "count": row.count}
        for row in db.execute(subj_stmt).all()
        if row.subject is not None
    ]

    # ── Task-type facet ──────────────────────────────────────────────────────
    tt_stmt = _apply_filter(
        select(Dataset.task_type, func.count(Example.id).label("count"))
        .join(Dataset, Example.dataset_id == Dataset.id)
        .group_by(Dataset.task_type)
        .order_by(Dataset.task_type),
        query,
    )
    task_types = [{"name": row.task_type, "count": row.count} for row in db.execute(tt_stmt).all()]

    # ── Total ────────────────────────────────────────────────────────────────
    total_stmt = _apply_filter(
        select(func.count(Example.id)).join(Dataset, Example.dataset_id == Dataset.id),
        query,
    )
    total = db.execute(total_stmt).scalar() or 0

    return {
        "datasets": datasets,
        "subjects": subjects,
        "task_types": task_types,
        "total": total,
    }
