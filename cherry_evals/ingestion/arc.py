"""ARC (AI2 Reasoning Challenge) dataset ingestion."""

from typing import Any

from cherry_evals.ingestion.base import DatasetAdapter
from db.postgres.models import Example


def _format_arc_choices(choices_field: dict[str, Any]) -> list[str]:
    """Format ARC choices dict into 'A: text' strings.

    The ARC choices field has the shape:
        {"text": ["text A", "text B", ...], "label": ["A", "B", ...]}
    """
    texts: list[str] = choices_field.get("text", [])
    labels: list[str] = choices_field.get("label", [])

    return [f"{label}: {text}" for label, text in zip(labels, texts)]


class ARCAdapter(DatasetAdapter):
    """Adapter for the ARC-Challenge science QA benchmark."""

    @property
    def name(self) -> str:
        return "ARC"

    @property
    def source(self) -> str:
        return "HuggingFace:allenai/ai2_arc"

    @property
    def hf_dataset_id(self) -> str:
        return "allenai/ai2_arc"

    @property
    def hf_config(self) -> str:
        return "ARC-Challenge"

    @property
    def license(self) -> str:
        return "CC-BY-SA-4.0"

    @property
    def task_type(self) -> str:
        return "science_qa"

    @property
    def description(self) -> str:
        return (
            "ARC-Challenge: the harder subset of the AI2 Reasoning Challenge, "
            "consisting of genuine grade-school science questions."
        )

    @property
    def splits(self) -> list[str]:
        return ["train", "validation", "test"]

    def parse_example(self, row: dict[str, Any], dataset_id: int, split: str) -> Example:
        """Parse a single ARC row into an Example object.

        ARC format:
        - id: str (unique question identifier)
        - question: str
        - choices: dict with "text" (list[str]) and "label" (list[str]) keys
        - answerKey: str (correct choice label, e.g. "A", "B", "C", or "D")
        """
        choices_field: dict[str, Any] = row.get("choices", {})
        formatted_choices = _format_arc_choices(choices_field)

        metadata: dict[str, Any] = {
            "question_id": row.get("id", ""),
            "split": split,
            "difficulty": "challenge",
        }

        return Example(
            dataset_id=dataset_id,
            question=row.get("question", ""),
            answer=row.get("answerKey"),
            choices=formatted_choices,
            example_metadata=metadata,
        )
