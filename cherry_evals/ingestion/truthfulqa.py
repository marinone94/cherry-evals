"""TruthfulQA dataset ingestion."""

from typing import Any

from cherry_evals.ingestion.base import DatasetAdapter
from db.postgres.models import Example

_CHOICE_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _mc1_correct_letter(mc1_targets: dict[str, Any]) -> str | None:
    """Return the letter of the single correct answer in mc1_targets.

    mc1_targets has the shape:
        {"choices": ["choice A text", ...], "labels": [0, 1, 0, ...]}
    where exactly one label is 1 (correct).
    """
    labels: list[int] = mc1_targets.get("labels", [])

    for idx, label in enumerate(labels):
        if label == 1 and idx < len(_CHOICE_LETTERS):
            return _CHOICE_LETTERS[idx]

    return None


class TruthfulQAAdapter(DatasetAdapter):
    """Adapter for the TruthfulQA multiple-choice benchmark."""

    @property
    def name(self) -> str:
        return "TruthfulQA"

    @property
    def source(self) -> str:
        return "HuggingFace:truthfulqa/truthful_qa"

    @property
    def hf_dataset_id(self) -> str:
        return "truthfulqa/truthful_qa"

    @property
    def hf_config(self) -> str:
        return "multiple_choice"

    @property
    def license(self) -> str:
        return "Apache-2.0"

    @property
    def task_type(self) -> str:
        return "truthfulness"

    @property
    def description(self) -> str:
        return (
            "TruthfulQA: a benchmark to measure whether language models generate "
            "truthful answers to questions that may elicit false beliefs."
        )

    @property
    def splits(self) -> list[str]:
        return ["validation"]

    def parse_example(self, row: dict[str, Any], dataset_id: int, split: str) -> Example:
        """Parse a single TruthfulQA (multiple_choice) row into an Example object.

        TruthfulQA multiple_choice format:
        - question: str
        - mc1_targets: dict with keys "choices" (list[str]) and "labels" (list[int])
          where exactly one label is 1 (correct answer)
        - mc2_targets: dict (same shape, multiple correct answers — not used here)
        """
        mc1: dict[str, Any] = row.get("mc1_targets", {})
        choices_text: list[str] = mc1.get("choices", [])

        formatted_choices = [
            f"{_CHOICE_LETTERS[i]}: {text}"
            for i, text in enumerate(choices_text)
            if i < len(_CHOICE_LETTERS)
        ]

        metadata: dict[str, Any] = {"split": split}

        return Example(
            dataset_id=dataset_id,
            question=row.get("question", ""),
            answer=_mc1_correct_letter(mc1),
            choices=formatted_choices,
            example_metadata=metadata,
        )
