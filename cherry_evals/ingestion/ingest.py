"""Generic dataset ingestion function."""

from typing import Any

from datasets import load_dataset
from sqlalchemy import select
from sqlalchemy.orm import Session

from cherry_evals.ingestion.base import DatasetAdapter
from db.postgres.base import SessionLocal
from db.postgres.models import Dataset, Example


def ingest_dataset(
    adapter: DatasetAdapter,
    batch_size: int = 1000,
    limit: int | None = None,
) -> dict[str, Any]:
    """Ingest a dataset from HuggingFace using the given adapter.

    Args:
        adapter: DatasetAdapter instance describing how to fetch and parse the dataset.
        batch_size: Number of examples to insert per batch.
        limit: Optional limit on total number of examples to ingest (for testing).

    Returns:
        Dictionary with ingestion statistics.
    """
    print(f"Downloading {adapter.name} dataset from HuggingFace...")

    # Load with or without a config name
    if adapter.hf_config is not None:
        hf_dataset = load_dataset(adapter.hf_dataset_id, adapter.hf_config)
    else:
        hf_dataset = load_dataset(adapter.hf_dataset_id)

    db = SessionLocal()

    try:
        dataset_record = _get_or_create_dataset(db, adapter)

        total_examples = 0
        examples_by_split: dict[str, int] = {}

        for split_name in adapter.splits:
            if split_name not in hf_dataset:
                print(f"  Skipping split '{split_name}' (not present in dataset)")
                continue

            split_data = hf_dataset[split_name]
            split_examples: list[Example] = []

            num_examples = len(split_data)
            if limit is not None:
                remaining = limit - total_examples
                if remaining <= 0:
                    break
                num_examples = min(num_examples, remaining)

            print(f"  Processing split '{split_name}': {num_examples} examples")

            for i in range(num_examples):
                row = split_data[i]
                example = adapter.parse_example(row, dataset_record.id, split_name)
                split_examples.append(example)

                if len(split_examples) >= batch_size:
                    db.bulk_save_objects(split_examples)
                    db.commit()
                    split_examples = []

                total_examples += 1

            if split_examples:
                db.bulk_save_objects(split_examples)
                db.commit()

            examples_by_split[split_name] = num_examples

        # Build stats: start with split counts, then merge adapter-specific stats
        base_stats: dict[str, Any] = {
            "total_examples": total_examples,
            "splits": examples_by_split,
        }
        custom_stats = adapter.compute_stats(db, dataset_record.id)
        dataset_record.stats = {**base_stats, **custom_stats}
        db.commit()

        stats: dict[str, Any] = {
            "dataset_id": dataset_record.id,
            "dataset_name": dataset_record.name,
            "total_examples": total_examples,
            "splits": examples_by_split,
        }

        print(f"Ingested {total_examples} examples from {adapter.name}")
        return stats

    finally:
        db.close()


def _get_or_create_dataset(db: Session, adapter: DatasetAdapter) -> Dataset:
    """Get or create a Dataset record for the given adapter."""
    stmt = select(Dataset).where(Dataset.name == adapter.name)
    result = db.execute(stmt)
    dataset = result.scalar_one_or_none()

    if dataset is None:
        dataset = Dataset(
            name=adapter.name,
            source=adapter.source,
            license=adapter.license,
            task_type=adapter.task_type,
            description=adapter.description,
            stats={},
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        print(f"  Created dataset record '{adapter.name}' (id={dataset.id})")
    else:
        # Clear old examples so re-ingestion is idempotent
        db.query(Example).filter(Example.dataset_id == dataset.id).delete()
        db.commit()
        print(
            f"  Using existing dataset record '{adapter.name}' (id={dataset.id}),"
            " cleared old examples"
        )

    return dataset
