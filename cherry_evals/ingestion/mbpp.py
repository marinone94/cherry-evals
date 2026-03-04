"""MBPP (Mostly Basic Python Problems) dataset ingestion."""

from typing import Any

from cherry_evals.ingestion.base import DatasetAdapter
from db.postgres.models import Example


class MBPPAdapter(DatasetAdapter):
    """Adapter for the MBPP code generation benchmark."""

    @property
    def name(self) -> str:
        return "MBPP"

    @property
    def source(self) -> str:
        return "HuggingFace:google-research-datasets/mbpp"

    @property
    def hf_dataset_id(self) -> str:
        return "google-research-datasets/mbpp"

    @property
    def hf_config(self) -> str:
        return "full"

    @property
    def license(self) -> str:
        return "CC-BY-4.0"

    @property
    def task_type(self) -> str:
        return "code_generation"

    @property
    def description(self) -> str:
        return (
            "MBPP: Mostly Basic Python Problems — a benchmark of ~1000 crowd-sourced Python "
            "programming problems with solutions and automated tests."
        )

    @property
    def splits(self) -> list[str]:
        return ["train", "validation", "test"]

    def parse_example(self, row: dict[str, Any], dataset_id: int, split: str) -> Example:
        """Parse a single MBPP row into an Example object.

        MBPP format:
        - task_id: int (unique problem identifier)
        - text: str (problem description / prompt)
        - code: str (canonical Python solution)
        - test_list: list[str] (assert-based test cases)
        - test_setup_code: str (setup code required before running tests)
        - challenge_test_list: list[str] (harder test cases)
        """
        test_list: list[str] = row.get("test_list") or []
        challenge_test_list: list[str] = row.get("challenge_test_list") or []

        metadata: dict[str, Any] = {
            "task_id": row.get("task_id", ""),
            "num_tests": len(test_list),
            "has_challenge_tests": bool(challenge_test_list),
            "split": split,
        }

        return Example(
            dataset_id=dataset_id,
            question=row.get("text", ""),
            answer=row.get("code") or None,
            choices=None,
            example_metadata=metadata,
        )
