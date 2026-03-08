"""PIQA (Physical Intuition QA) dataset ingestion."""

from typing import Any

from cherry_evals.ingestion.base import DatasetAdapter
from db.postgres.models import Example

# Maps the integer label to a letter label
_LABEL_TO_LETTER: dict[int, str] = {0: "A", 1: "B"}


class PIQAAdapter(DatasetAdapter):
    """Adapter for the PIQA physical intuition benchmark."""

    @property
    def name(self) -> str:
        return "PIQA"

    @property
    def source(self) -> str:
        return "HuggingFace:ybisk/piqa"

    @property
    def hf_dataset_id(self) -> str:
        return "ybisk/piqa"

    @property
    def hf_config(self) -> None:
        return None

    @property
    def hf_revision(self) -> str:
        return "refs/convert/parquet"

    @property
    def license(self) -> str:
        return "AFL-3.0"

    @property
    def task_type(self) -> str:
        return "physical_intuition"

    @property
    def description(self) -> str:
        return (
            "PIQA: Physical Intuition Question Answering benchmark that tests understanding "
            "of everyday physical processes and goals."
        )

    @property
    def splits(self) -> list[str]:
        # The test split labels are -1 (withheld); only train + validation are ingested.
        return ["train", "validation"]

    def parse_example(self, row: dict[str, Any], dataset_id: int, split: str) -> Example:
        """Parse a single PIQA row into an Example object.

        PIQA format:
        - goal: str (physical task or goal)
        - sol1: str (first candidate solution)
        - sol2: str (second candidate solution)
        - label: int (0 for sol1, 1 for sol2)
        """
        sol1: str = row.get("sol1", "")
        sol2: str = row.get("sol2", "")
        label: Any = row.get("label", None)

        # Convert int label to letter; handle None or unexpected values gracefully
        answer_letter: str | None
        if isinstance(label, int):
            answer_letter = _LABEL_TO_LETTER.get(label)
        else:
            answer_letter = None

        formatted_choices = [f"A: {sol1}", f"B: {sol2}"]

        metadata: dict[str, Any] = {
            "split": split,
        }

        return Example(
            dataset_id=dataset_id,
            question=row.get("goal", ""),
            answer=answer_letter,
            choices=formatted_choices,
            example_metadata=metadata,
        )
