"""Adapter registry: maps lowercase dataset names to adapter classes."""

from cherry_evals.ingestion.arc import ARCAdapter
from cherry_evals.ingestion.base import DatasetAdapter
from cherry_evals.ingestion.boolq import BoolQAdapter
from cherry_evals.ingestion.gsm8k import GSM8KAdapter
from cherry_evals.ingestion.hellaswag import HellaSwagAdapter
from cherry_evals.ingestion.humaneval import HumanEvalAdapter
from cherry_evals.ingestion.mbpp import MBPPAdapter
from cherry_evals.ingestion.mmlu import MMLUAdapter
from cherry_evals.ingestion.piqa import PIQAAdapter
from cherry_evals.ingestion.truthfulqa import TruthfulQAAdapter
from cherry_evals.ingestion.winogrande import WinoGrandeAdapter

# Maps the CLI-friendly lowercase key to the adapter class.
# Instantiate adapters on demand — they carry no mutable state.
ADAPTER_REGISTRY: dict[str, type[DatasetAdapter]] = {
    "mmlu": MMLUAdapter,
    "humaneval": HumanEvalAdapter,
    "gsm8k": GSM8KAdapter,
    "hellaswag": HellaSwagAdapter,
    "truthfulqa": TruthfulQAAdapter,
    "arc": ARCAdapter,
    "winogrande": WinoGrandeAdapter,
    "piqa": PIQAAdapter,
    "mbpp": MBPPAdapter,
    "boolq": BoolQAdapter,
}
