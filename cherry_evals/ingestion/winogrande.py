"""WinoGrande dataset ingestion."""

from typing import Any

from cherry_evals.ingestion.base import DatasetAdapter
from db.postgres.models import Example

# Maps the string answer value to a letter label
_ANSWER_TO_LETTER: dict[str, str] = {"1": "A", "2": "B"}


class WinoGrandeAdapter(DatasetAdapter):
    """Adapter for the WinoGrande commonsense reasoning benchmark."""

    @property
    def name(self) -> str:
        return "WinoGrande"

    @property
    def source(self) -> str:
        return "HuggingFace:allenai/winogrande"

    @property
    def hf_dataset_id(self) -> str:
        return "allenai/winogrande"

    @property
    def hf_config(self) -> str:
        return "winogrande_xl"

    @property
    def license(self) -> str:
        return "Apache-2.0"

    @property
    def task_type(self) -> str:
        return "commonsense_reasoning"

    @property
    def description(self) -> str:
        return (
            "WinoGrande: a large-scale dataset for commonsense reasoning based on Winograd Schema "
            "challenge, requiring resolving pronoun/entity coreference using world knowledge."
        )

    @property
    def splits(self) -> list[str]:
        # The test split labels are withheld; only train + validation are ingested.
        return ["train", "validation"]

    def parse_example(self, row: dict[str, Any], dataset_id: int, split: str) -> Example:
        """Parse a single WinoGrande row into an Example object.

        WinoGrande format:
        - sentence: str (sentence with a '_' blank to fill in)
        - option1: str (first candidate to fill the blank)
        - option2: str (second candidate to fill the blank)
        - answer: str ("1" for option1, "2" for option2)
        """
        option1: str = row.get("option1", "")
        option2: str = row.get("option2", "")
        raw_answer: str = str(row.get("answer", ""))

        # Convert "1"/"2" to letter; fall back to None for unknown values
        answer_letter: str | None = _ANSWER_TO_LETTER.get(raw_answer)

        formatted_choices = [f"A: {option1}", f"B: {option2}"]

        metadata: dict[str, Any] = {
            "split": split,
        }

        return Example(
            dataset_id=dataset_id,
            question=row.get("sentence", ""),
            answer=answer_letter,
            choices=formatted_choices,
            example_metadata=metadata,
        )
