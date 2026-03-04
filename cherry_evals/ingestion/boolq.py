"""BoolQ dataset ingestion."""

from typing import Any

from cherry_evals.ingestion.base import DatasetAdapter
from db.postgres.models import Example

# Maximum number of characters to include from the passage in metadata
_PASSAGE_EXCERPT_CHARS = 500


class BoolQAdapter(DatasetAdapter):
    """Adapter for the BoolQ reading comprehension benchmark."""

    @property
    def name(self) -> str:
        return "BoolQ"

    @property
    def source(self) -> str:
        return "HuggingFace:google/boolq"

    @property
    def hf_dataset_id(self) -> str:
        return "google/boolq"

    @property
    def hf_config(self) -> None:
        return None

    @property
    def license(self) -> str:
        return "CC-BY-SA-3.0"

    @property
    def task_type(self) -> str:
        return "reading_comprehension"

    @property
    def description(self) -> str:
        return (
            "BoolQ: a reading comprehension dataset of naturally-occurring yes/no questions "
            "paired with Wikipedia passages that contain the answer."
        )

    @property
    def splits(self) -> list[str]:
        return ["train", "validation"]

    def parse_example(self, row: dict[str, Any], dataset_id: int, split: str) -> Example:
        """Parse a single BoolQ row into an Example object.

        BoolQ format:
        - question: str (the yes/no question)
        - answer: bool (True for Yes, False for No)
        - passage: str (Wikipedia passage containing the answer)
        """
        raw_answer: Any = row.get("answer", None)
        passage: str = row.get("passage", "")

        # Convert bool to "Yes"/"No"; handle None gracefully
        answer_str: str | None
        if isinstance(raw_answer, bool):
            answer_str = "Yes" if raw_answer else "No"
        else:
            answer_str = None

        metadata: dict[str, Any] = {
            "passage": passage[:_PASSAGE_EXCERPT_CHARS],
            "split": split,
        }

        return Example(
            dataset_id=dataset_id,
            question=row.get("question", ""),
            answer=answer_str,
            choices=["A: Yes", "B: No"],
            example_metadata=metadata,
        )
