"""Verify MMLU dataset ingestion."""

from sqlalchemy import func, select

from db.postgres.base import SessionLocal
from db.postgres.models import Dataset, Example

db = SessionLocal()

try:
    # Get dataset
    stmt = select(Dataset).where(Dataset.name == "MMLU")
    dataset = db.execute(stmt).scalar_one_or_none()

    if dataset:
        print(f"Dataset: {dataset.name}")
        print(f"Source: {dataset.source}")
        print(f"Task Type: {dataset.task_type}")
        print(f"License: {dataset.license}")
        print(f"\nStats: {dataset.stats}")

        # Get example counts
        total = db.query(func.count(Example.id)).filter(Example.dataset_id == dataset.id).scalar()
        print(f"\nTotal examples in DB: {total}")

        # Sample examples
        print("\n=== Sample Examples ===")
        examples = db.query(Example).filter(Example.dataset_id == dataset.id).limit(3).all()
        for i, ex in enumerate(examples, 1):
            print(f"\nExample {i}:")
            print(f"  Question: {ex.question[:100]}...")
            print(f"  Choices: {ex.choices}")
            print(f"  Answer: {ex.answer}")
            print(f"  Metadata: {ex.example_metadata}")
    else:
        print("MMLU dataset not found")

finally:
    db.close()
