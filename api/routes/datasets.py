"""Dataset API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.models.datasets import DatasetListResponse, DatasetResponse
from db.postgres.base import get_db
from db.postgres.models import Dataset, Example

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=DatasetListResponse)
def list_datasets(db: Session = Depends(get_db)):
    """List all available datasets."""
    datasets = db.execute(select(Dataset).order_by(Dataset.name)).scalars().all()
    return DatasetListResponse(
        datasets=[DatasetResponse.model_validate(d) for d in datasets],
        total=len(datasets),
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Get a single dataset by ID."""
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetResponse.model_validate(dataset)


@router.get("/{dataset_id}/stats")
def get_dataset_stats(dataset_id: int, db: Session = Depends(get_db)):
    """Get dataset statistics including example count and subject distribution."""
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    example_count = db.execute(
        select(func.count(Example.id)).where(Example.dataset_id == dataset_id)
    ).scalar()

    return {
        "dataset_id": dataset_id,
        "dataset_name": dataset.name,
        "example_count": example_count,
        "stats": dataset.stats,
    }


@router.get("/{dataset_id}/subjects")
def get_dataset_subjects(dataset_id: int, db: Session = Depends(get_db)):
    """Return the subject breakdown for a specific dataset.

    Each entry contains the subject name and the number of examples with that subject.
    Examples without a subject in their metadata are excluded.
    """
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    rows = db.execute(
        select(
            Example.example_metadata["subject"].as_string().label("subject"),
            func.count(Example.id).label("count"),
        )
        .where(Example.dataset_id == dataset_id)
        .where(Example.example_metadata["subject"].as_string() != None)  # noqa: E711
        .group_by(Example.example_metadata["subject"].as_string())
        .order_by(Example.example_metadata["subject"].as_string())
    ).all()

    subjects = [
        {"subject": row.subject, "count": row.count} for row in rows if row.subject is not None
    ]

    return {"dataset_id": dataset_id, "dataset_name": dataset.name, "subjects": subjects}
