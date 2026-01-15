"""MMLU dataset ingestion."""

from typing import Any

from datasets import load_dataset
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.postgres.base import SessionLocal
from db.postgres.models import Dataset, Example


def ingest_mmlu(batch_size: int = 1000, limit: int | None = None) -> dict[str, Any]:
    """Ingest MMLU dataset from HuggingFace.

    Args:
        batch_size: Number of examples to insert per batch
        limit: Optional limit on number of examples to ingest (for testing)

    Returns:
        Dictionary with ingestion statistics
    """
    # Step 1: Download MMLU dataset from HuggingFace
    print("Downloading MMLU dataset from HuggingFace...")
    dataset = load_dataset("cais/mmlu", "all")

    # Create database session
    db = SessionLocal()

    try:
        # Step 2: Create or get dataset record
        mmlu_dataset = _get_or_create_dataset(db)

        # Step 3: Parse and store examples
        total_examples = 0
        examples_by_split = {}

        for split_name in ["test", "validation", "dev"]:
            if split_name not in dataset:
                continue

            split_data = dataset[split_name]
            split_examples = []

            # Determine how many examples to process for this split
            num_examples = len(split_data)
            if limit is not None:
                remaining = limit - total_examples
                if remaining <= 0:
                    break
                num_examples = min(num_examples, remaining)

            print(f"Processing {split_name} split: {num_examples} examples")

            for i in range(num_examples):
                row = split_data[i]

                # Step 3: Parse and normalize to Example schema
                example = _parse_mmlu_example(row, mmlu_dataset.id, split_name)
                split_examples.append(example)

                # Batch insert
                if len(split_examples) >= batch_size:
                    db.bulk_save_objects(split_examples)
                    db.commit()
                    split_examples = []

                total_examples += 1

            # Insert remaining examples
            if split_examples:
                db.bulk_save_objects(split_examples)
                db.commit()

            examples_by_split[split_name] = num_examples

        # Update dataset stats
        mmlu_dataset.stats = {
            "total_examples": total_examples,
            "splits": examples_by_split,
            "subjects": _count_subjects(db, mmlu_dataset.id),
        }
        db.commit()

        stats = {
            "dataset_id": mmlu_dataset.id,
            "dataset_name": mmlu_dataset.name,
            "total_examples": total_examples,
            "splits": examples_by_split,
        }

        print(f"✓ Ingested {total_examples} examples from MMLU")
        return stats

    finally:
        db.close()


def _get_or_create_dataset(db: Session) -> Dataset:
    """Get or create the MMLU dataset record."""
    stmt = select(Dataset).where(Dataset.name == "MMLU")
    result = db.execute(stmt)
    dataset = result.scalar_one_or_none()

    if dataset is None:
        dataset = Dataset(
            name="MMLU",
            source="HuggingFace:cais/mmlu",
            license="MIT",
            task_type="multiple_choice",
            description="Massive Multitask Language Understanding (MMLU) benchmark",
            stats={},
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        print(f"Created MMLU dataset record (id={dataset.id})")
    else:
        # Delete existing examples to re-ingest
        db.query(Example).filter(Example.dataset_id == dataset.id).delete()
        db.commit()
        print(f"Using existing MMLU dataset record (id={dataset.id}), cleared old examples")

    return dataset


def _parse_mmlu_example(row: dict[str, Any], dataset_id: int, split: str) -> Example:
    """Parse a single MMLU row into an Example object.

    MMLU format:
    - question: str
    - choices: list[str] (typically 4 choices: A, B, C, D)
    - answer: int (index of correct answer, 0-3)
    - subject: str (e.g., "abstract_algebra", "anatomy", etc.)
    """
    # Extract fields
    question = row.get("question", "")
    choices = row.get("choices", [])
    answer_idx = row.get("answer", 0)
    subject = row.get("subject", "unknown")

    # Convert answer index to letter (0 -> "A", 1 -> "B", etc.)
    answer_letter = chr(65 + answer_idx) if 0 <= answer_idx < len(choices) else None

    # Format choices as "A: ..., B: ..., C: ..., D: ..."
    formatted_choices = [f"{chr(65 + i)}: {choice}" for i, choice in enumerate(choices)]

    # Extract metadata
    metadata = {
        "subject": subject,
        "split": split,
        "answer_index": answer_idx,
        "num_choices": len(choices),
    }

    return Example(
        dataset_id=dataset_id,
        question=question,
        answer=answer_letter,
        choices=formatted_choices,
        example_metadata=metadata,
    )


def _count_subjects(db: Session, dataset_id: int) -> dict[str, int]:
    """Count examples by subject for the given dataset."""
    from sqlalchemy import String, cast, func

    subject_col = cast(Example.example_metadata["subject"], String)
    results = (
        db.query(subject_col, func.count(Example.id))
        .filter(Example.dataset_id == dataset_id)
        .group_by(subject_col)
        .all()
    )

    return {subject: count for subject, count in results}
