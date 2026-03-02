"""Example API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.models.examples import ExampleListResponse, ExampleResponse
from db.postgres.base import get_db
from db.postgres.models import Example

router = APIRouter(prefix="/examples", tags=["examples"])


@router.get("", response_model=ExampleListResponse)
def list_examples(
    dataset_id: int | None = Query(None, description="Filter by dataset ID"),
    subject: str | None = Query(None, description="Filter by subject (in metadata)"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    """List examples with optional filters and pagination."""
    query = select(Example)
    count_query = select(func.count(Example.id))

    if dataset_id is not None:
        query = query.where(Example.dataset_id == dataset_id)
        count_query = count_query.where(Example.dataset_id == dataset_id)

    # Filter by subject in example_metadata JSON
    if subject is not None:
        query = query.where(Example.example_metadata["subject"].as_string() == subject)
        count_query = count_query.where(Example.example_metadata["subject"].as_string() == subject)

    total = db.execute(count_query).scalar()

    examples = db.execute(query.order_by(Example.id).offset(offset).limit(limit)).scalars().all()

    return ExampleListResponse(
        examples=[ExampleResponse.model_validate(e) for e in examples],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{example_id}", response_model=ExampleResponse)
def get_example(example_id: int, db: Session = Depends(get_db)):
    """Get a single example by ID."""
    example = db.get(Example, example_id)
    if not example:
        raise HTTPException(status_code=404, detail="Example not found")
    return ExampleResponse.model_validate(example)
