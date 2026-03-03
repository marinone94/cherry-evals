"""GSM8K dataset ingestion."""

import re
from typing import Any

from cherry_evals.ingestion.base import DatasetAdapter
from db.postgres.models import Example

# GSM8K uses "####" as a delimiter before the final numeric answer.
_FINAL_ANSWER_RE = re.compile(r"####\s*([\d,\.\-]+)")


def _extract_final_answer(answer_text: str) -> str | None:
    """Extract the numeric answer that follows '####' in a GSM8K answer string."""
    match = _FINAL_ANSWER_RE.search(answer_text)
    if match:
        # Strip commas used as thousands separators
        return match.group(1).replace(",", "")
    return None


class GSM8KAdapter(DatasetAdapter):
    """Adapter for the GSM8K grade-school math reasoning benchmark."""

    @property
    def name(self) -> str:
        return "GSM8K"

    @property
    def source(self) -> str:
        return "HuggingFace:openai/gsm8k"

    @property
    def hf_dataset_id(self) -> str:
        return "openai/gsm8k"

    @property
    def hf_config(self) -> str:
        return "main"

    @property
    def license(self) -> str:
        return "MIT"

    @property
    def task_type(self) -> str:
        return "math_reasoning"

    @property
    def description(self) -> str:
        return (
            "GSM8K: 8.5K grade school math word problems requiring multi-step reasoning, "
            "with chain-of-thought solutions."
        )

    @property
    def splits(self) -> list[str]:
        return ["train", "test"]

    def parse_example(self, row: dict[str, Any], dataset_id: int, split: str) -> Example:
        """Parse a single GSM8K row into an Example object.

        GSM8K format:
        - question: str
        - answer: str (chain-of-thought reasoning ending with "#### <number>")
        """
        answer_text: str = row.get("answer", "")

        metadata: dict[str, Any] = {
            "split": split,
            "final_answer": _extract_final_answer(answer_text),
        }

        return Example(
            dataset_id=dataset_id,
            question=row.get("question", ""),
            answer=answer_text,
            choices=None,
            example_metadata=metadata,
        )
