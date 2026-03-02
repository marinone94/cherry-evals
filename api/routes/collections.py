"""Collection API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.models.collections import (
    AddExamplesRequest,
    CollectionCreate,
    CollectionExampleResponse,
    CollectionExamplesListResponse,
    CollectionListResponse,
    CollectionResponse,
    CollectionUpdate,
    RemoveExamplesRequest,
)
from db.postgres.base import get_db
from db.postgres.models import Collection, CollectionExample, Example

router = APIRouter(prefix="/collections", tags=["collections"])


def _collection_to_response(db: Session, collection: Collection) -> CollectionResponse:
    """Convert a Collection ORM object to a response with example_count."""
    example_count = db.execute(
        select(func.count(CollectionExample.id)).where(
            CollectionExample.collection_id == collection.id
        )
    ).scalar()

    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        user_id=collection.user_id,
        example_count=example_count,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


@router.post("", response_model=CollectionResponse, status_code=201)
def create_collection(request: CollectionCreate, db: Session = Depends(get_db)):
    """Create a new collection."""
    collection = Collection(name=request.name, description=request.description)
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return _collection_to_response(db, collection)


@router.get("", response_model=CollectionListResponse)
def list_collections(db: Session = Depends(get_db)):
    """List all collections."""
    collections = (
        db.execute(select(Collection).order_by(Collection.created_at.desc())).scalars().all()
    )

    return CollectionListResponse(
        collections=[_collection_to_response(db, c) for c in collections],
        total=len(collections),
    )


@router.get("/{collection_id}", response_model=CollectionResponse)
def get_collection(collection_id: int, db: Session = Depends(get_db)):
    """Get a single collection by ID."""
    collection = db.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return _collection_to_response(db, collection)


@router.put("/{collection_id}", response_model=CollectionResponse)
def update_collection(collection_id: int, request: CollectionUpdate, db: Session = Depends(get_db)):
    """Update collection metadata."""
    collection = db.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if request.name is not None:
        collection.name = request.name
    if request.description is not None:
        collection.description = request.description

    db.commit()
    db.refresh(collection)
    return _collection_to_response(db, collection)


@router.delete("/{collection_id}", status_code=204)
def delete_collection(collection_id: int, db: Session = Depends(get_db)):
    """Delete a collection and all its example associations."""
    collection = db.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    db.delete(collection)
    db.commit()


@router.get("/{collection_id}/examples", response_model=CollectionExamplesListResponse)
def list_collection_examples(collection_id: int, db: Session = Depends(get_db)):
    """List all examples in a collection."""
    collection = db.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    rows = db.execute(
        select(Example, CollectionExample.added_at)
        .join(CollectionExample, CollectionExample.example_id == Example.id)
        .where(CollectionExample.collection_id == collection_id)
        .order_by(CollectionExample.added_at)
    ).all()

    examples = []
    for example, added_at in rows:
        examples.append(
            CollectionExampleResponse(
                id=example.id,
                dataset_id=example.dataset_id,
                question=example.question,
                answer=example.answer,
                choices=example.choices,
                example_metadata=example.example_metadata,
                added_at=added_at,
            )
        )

    return CollectionExamplesListResponse(
        examples=examples,
        total=len(examples),
        collection_id=collection_id,
    )


@router.post("/{collection_id}/examples", status_code=201)
def add_examples(collection_id: int, request: AddExamplesRequest, db: Session = Depends(get_db)):
    """Add examples to a collection by ID. Skips duplicates."""
    collection = db.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Check which examples already exist in collection
    existing = set(
        db.execute(
            select(CollectionExample.example_id).where(
                CollectionExample.collection_id == collection_id,
                CollectionExample.example_id.in_(request.example_ids),
            )
        )
        .scalars()
        .all()
    )

    added = 0
    for example_id in request.example_ids:
        if example_id in existing:
            continue

        # Verify the example exists
        example = db.get(Example, example_id)
        if not example:
            continue

        db.add(CollectionExample(collection_id=collection_id, example_id=example_id))
        added += 1

    db.commit()
    return {"added": added, "skipped": len(request.example_ids) - added}


@router.delete("/{collection_id}/examples/{example_id}", status_code=204)
def remove_example(collection_id: int, example_id: int, db: Session = Depends(get_db)):
    """Remove a single example from a collection."""
    ce = db.execute(
        select(CollectionExample).where(
            CollectionExample.collection_id == collection_id,
            CollectionExample.example_id == example_id,
        )
    ).scalar_one_or_none()

    if not ce:
        raise HTTPException(status_code=404, detail="Example not in collection")

    db.delete(ce)
    db.commit()


@router.post("/{collection_id}/examples/bulk-remove", status_code=200)
def bulk_remove_examples(
    collection_id: int, request: RemoveExamplesRequest, db: Session = Depends(get_db)
):
    """Remove multiple examples from a collection."""
    collection = db.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    ces = (
        db.execute(
            select(CollectionExample).where(
                CollectionExample.collection_id == collection_id,
                CollectionExample.example_id.in_(request.example_ids),
            )
        )
        .scalars()
        .all()
    )

    removed = len(ces)
    for ce in ces:
        db.delete(ce)
    db.commit()

    return {"removed": removed}
