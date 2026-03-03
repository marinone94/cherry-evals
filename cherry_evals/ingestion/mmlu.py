"""MMLU dataset ingestion."""

from typing import Any

from sqlalchemy import String, cast, func
from sqlalchemy.orm import Session

from cherry_evals.ingestion.base import DatasetAdapter
from cherry_evals.ingestion.ingest import ingest_dataset
from db.postgres.models import Example


class MMLUAdapter(DatasetAdapter):
    """Adapter for the MMLU (Massive Multitask Language Understanding) benchmark."""

    @property
    def name(self) -> str:
        return "MMLU"

    @property
    def source(self) -> str:
        return "HuggingFace:cais/mmlu"

    @property
    def hf_dataset_id(self) -> str:
        return "cais/mmlu"

    @property
    def hf_config(self) -> str:
        return "all"

    @property
    def license(self) -> str:
        return "MIT"

    @property
    def task_type(self) -> str:
        return "multiple_choice"

    @property
    def description(self) -> str:
        return "Massive Multitask Language Understanding (MMLU) benchmark"

    @property
    def splits(self) -> list[str]:
        return ["test", "validation", "dev"]

    def parse_example(self, row: dict[str, Any], dataset_id: int, split: str) -> Example:
        """Parse a single MMLU row into an Example object.

        MMLU format:
        - question: str
        - choices: list[str] (typically 4 choices: A, B, C, D)
        - answer: int (index of correct answer, 0-3)
        - subject: str (e.g., "abstract_algebra", "anatomy", etc.)
        """
        question = row.get("question", "")
        choices = row.get("choices", [])
        answer_idx = row.get("answer", 0)
        subject = row.get("subject", "unknown")

        # Convert answer index to letter (0 -> "A", 1 -> "B", etc.)
        answer_letter = chr(65 + answer_idx) if 0 <= answer_idx < len(choices) else None

        # Format choices as "A: ...", "B: ...", etc.
        formatted_choices = [f"{chr(65 + i)}: {choice}" for i, choice in enumerate(choices)]

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

    def compute_stats(self, db: Session, dataset_id: int) -> dict[str, Any]:
        """Compute per-subject counts for MMLU."""
        subject_col = cast(Example.example_metadata["subject"], String)
        results = (
            db.query(subject_col, func.count(Example.id))
            .filter(Example.dataset_id == dataset_id)
            .group_by(subject_col)
            .all()
        )
        return {"subjects": {subject: count for subject, count in results}}


def ingest_mmlu(batch_size: int = 1000, limit: int | None = None) -> dict[str, Any]:
    """Ingest MMLU dataset from HuggingFace.

    Args:
        batch_size: Number of examples to insert per batch.
        limit: Optional limit on number of examples to ingest (for testing).

    Returns:
        Dictionary with ingestion statistics.
    """
    return ingest_dataset(MMLUAdapter(), batch_size=batch_size, limit=limit)
