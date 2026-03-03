"""HellaSwag dataset ingestion."""

from typing import Any

from cherry_evals.ingestion.base import DatasetAdapter
from db.postgres.models import Example

# Letters used to label HellaSwag ending choices
_CHOICE_LETTERS = "ABCD"


class HellaSwagAdapter(DatasetAdapter):
    """Adapter for the HellaSwag commonsense NLI benchmark."""

    @property
    def name(self) -> str:
        return "HellaSwag"

    @property
    def source(self) -> str:
        return "HuggingFace:Rowan/hellaswag"

    @property
    def hf_dataset_id(self) -> str:
        return "Rowan/hellaswag"

    @property
    def hf_config(self) -> None:
        return None

    @property
    def license(self) -> str:
        return "MIT"

    @property
    def task_type(self) -> str:
        return "commonsense_reasoning"

    @property
    def description(self) -> str:
        return (
            "HellaSwag: a challenge dataset for grounded commonsense inference, "
            "specifically sentence completion."
        )

    @property
    def splits(self) -> list[str]:
        # The test split labels are withheld for the leaderboard, so we skip it.
        return ["train", "validation"]

    def parse_example(self, row: dict[str, Any], dataset_id: int, split: str) -> Example:
        """Parse a single HellaSwag row into an Example object.

        HellaSwag format:
        - ctx: str (activity context / partial sentence)
        - endings: list[str] (4 candidate sentence completions)
        - label: str (index of correct ending as a string, e.g. "2")
        - activity_label: str (ActivityNet/WikiHow category)
        """
        endings: list[str] = row.get("endings", [])
        label_str: str = str(row.get("label", "0"))

        # Guard against missing or malformed label
        try:
            answer_idx = int(label_str)
        except ValueError:
            answer_idx = 0

        # Convert index to letter; fall back to "A" for out-of-range values
        answer_letter = (
            _CHOICE_LETTERS[answer_idx] if 0 <= answer_idx < len(_CHOICE_LETTERS) else "A"
        )

        # Format endings as "A: ...", "B: ...", etc.
        formatted_choices = [f"{_CHOICE_LETTERS[i]}: {ending}" for i, ending in enumerate(endings)]

        metadata: dict[str, Any] = {
            "activity_label": row.get("activity_label", ""),
            "split": split,
            "answer_index": answer_idx,
        }

        return Example(
            dataset_id=dataset_id,
            question=row.get("ctx", ""),
            answer=answer_letter,
            choices=formatted_choices,
            example_metadata=metadata,
        )
