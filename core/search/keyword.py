"""Keyword search using PostgreSQL ILIKE (simple text matching).

For MVP-0, we use ILIKE for simplicity. Full-text search with tsvector
can be added later as an optimization when we need it.
"""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from db.postgres.models import Dataset, Example


def keyword_search(
    db: Session,
    query: str,
    dataset_name: str | None = None,
    subject: str | None = None,
    task_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "relevance",
) -> tuple[list[dict], int]:
    """Search examples by keyword matching on question text.

    Args:
        db: Database session
        query: Search query string
        dataset_name: Optional filter by dataset name
        subject: Optional filter by subject in metadata
        task_type: Optional filter by Dataset.task_type
        limit: Max results to return
        offset: Pagination offset
        sort_by: One of "relevance" (by id), "newest" (created_at desc),
                 "dataset" (dataset name then question)

    Returns:
        Tuple of (list of result dicts, total count)
    """
    search_pattern = f"%{query}%"

    # Base query: join with dataset to get dataset_name
    base_filter = or_(
        Example.question.ilike(search_pattern),
        Example.answer.ilike(search_pattern),
    )

    stmt = select(Example, Dataset.name.label("dataset_name")).join(
        Dataset, Example.dataset_id == Dataset.id
    )
    count_stmt = select(func.count(Example.id)).join(Dataset, Example.dataset_id == Dataset.id)

    # Apply search filter
    stmt = stmt.where(base_filter)
    count_stmt = count_stmt.where(base_filter)

    # Apply optional filters
    if dataset_name is not None:
        stmt = stmt.where(Dataset.name == dataset_name)
        count_stmt = count_stmt.where(Dataset.name == dataset_name)

    if subject is not None:
        stmt = stmt.where(Example.example_metadata["subject"].as_string() == subject)
        count_stmt = count_stmt.where(Example.example_metadata["subject"].as_string() == subject)

    if task_type is not None:
        stmt = stmt.where(Dataset.task_type == task_type)
        count_stmt = count_stmt.where(Dataset.task_type == task_type)

    total = db.execute(count_stmt).scalar()

    # Apply sort order
    if sort_by == "newest":
        order = Example.created_at.desc()
    elif sort_by == "dataset":
        order = (Dataset.name, Example.question)
    else:
        # "relevance" — keep a stable ordering by id
        order = Example.id

    if sort_by == "dataset":
        stmt = stmt.order_by(Dataset.name, Example.question)
    else:
        stmt = stmt.order_by(order)

    rows = db.execute(stmt.offset(offset).limit(limit)).all()

    results = []
    for example, ds_name in rows:
        results.append(
            {
                "id": example.id,
                "dataset_id": example.dataset_id,
                "dataset_name": ds_name,
                "question": example.question,
                "answer": example.answer,
                "choices": example.choices,
                "example_metadata": example.example_metadata,
                "score": None,
            }
        )

    return results, total
