"""Base interface for dataset ingestion adapters."""

from abc import ABC, abstractmethod
from typing import Any

from db.postgres.models import Example


class DatasetAdapter(ABC):
    """Base class for dataset ingestion adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Dataset display name (e.g., 'MMLU', 'GSM8K')."""
        ...

    @property
    @abstractmethod
    def source(self) -> str:
        """HuggingFace dataset identifier (e.g., 'HuggingFace:cais/mmlu')."""
        ...

    @property
    @abstractmethod
    def hf_dataset_id(self) -> str:
        """HuggingFace dataset ID for load_dataset() (e.g., 'cais/mmlu')."""
        ...

    @property
    def hf_config(self) -> str | None:
        """HuggingFace dataset config/subset name. None for default."""
        return None

    @property
    def hf_revision(self) -> str | None:
        """HuggingFace dataset revision/branch. Use 'refs/convert/parquet' for legacy datasets."""
        return None

    @property
    @abstractmethod
    def license(self) -> str:
        """Dataset license."""
        ...

    @property
    @abstractmethod
    def task_type(self) -> str:
        """Task type (e.g., 'multiple_choice', 'code_generation')."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of the dataset."""
        ...

    @property
    @abstractmethod
    def splits(self) -> list[str]:
        """List of split names to ingest (e.g., ['test', 'validation'])."""
        ...

    @abstractmethod
    def parse_example(self, row: dict[str, Any], dataset_id: int, split: str) -> Example:
        """Parse a single HuggingFace row into an Example object."""
        ...

    def compute_stats(self, db: Any, dataset_id: int) -> dict[str, Any]:
        """Compute dataset-specific stats. Override for custom stats."""
        return {}
