"""HumanEval dataset ingestion."""

from typing import Any

from cherry_evals.ingestion.base import DatasetAdapter
from db.postgres.models import Example


class HumanEvalAdapter(DatasetAdapter):
    """Adapter for the OpenAI HumanEval coding benchmark."""

    @property
    def name(self) -> str:
        return "HumanEval"

    @property
    def source(self) -> str:
        return "HuggingFace:openai/openai_humaneval"

    @property
    def hf_dataset_id(self) -> str:
        return "openai/openai_humaneval"

    @property
    def hf_config(self) -> None:
        return None

    @property
    def license(self) -> str:
        return "MIT"

    @property
    def task_type(self) -> str:
        return "code_generation"

    @property
    def description(self) -> str:
        return (
            "HumanEval: a set of 164 hand-written Python programming problems "
            "used to measure functional code generation."
        )

    @property
    def splits(self) -> list[str]:
        return ["test"]

    def parse_example(self, row: dict[str, Any], dataset_id: int, split: str) -> Example:
        """Parse a single HumanEval row into an Example object.

        HumanEval format:
        - task_id: str (e.g., "HumanEval/0")
        - prompt: str (function signature + docstring)
        - canonical_solution: str (reference implementation)
        - entry_point: str (function name to call during evaluation)
        - test: str (test harness code)
        """
        metadata: dict[str, Any] = {
            "task_id": row.get("task_id", ""),
            "entry_point": row.get("entry_point", ""),
            "has_test": True,
            "split": split,
        }

        return Example(
            dataset_id=dataset_id,
            question=row.get("prompt", ""),
            answer=row.get("canonical_solution"),
            choices=None,
            example_metadata=metadata,
        )
