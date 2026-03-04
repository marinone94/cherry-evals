"""Unit tests for dataset ingestion adapters — batch 2 (WinoGrande, PIQA, MBPP, BoolQ)."""

import pytest

from cherry_evals.ingestion.base import DatasetAdapter
from cherry_evals.ingestion.boolq import BoolQAdapter
from cherry_evals.ingestion.mbpp import MBPPAdapter
from cherry_evals.ingestion.piqa import PIQAAdapter
from cherry_evals.ingestion.registry import ADAPTER_REGISTRY
from cherry_evals.ingestion.winogrande import WinoGrandeAdapter
from db.postgres.models import Example

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DATASET_ID = 99


# ---------------------------------------------------------------------------
# WinoGrande adapter — property tests
# ---------------------------------------------------------------------------


def test_winogrande_name():
    assert WinoGrandeAdapter().name == "WinoGrande"


def test_winogrande_source():
    assert WinoGrandeAdapter().source == "HuggingFace:allenai/winogrande"


def test_winogrande_hf_dataset_id():
    assert WinoGrandeAdapter().hf_dataset_id == "allenai/winogrande"


def test_winogrande_hf_config():
    assert WinoGrandeAdapter().hf_config == "winogrande_xl"


def test_winogrande_license():
    assert WinoGrandeAdapter().license == "Apache-2.0"


def test_winogrande_task_type():
    assert WinoGrandeAdapter().task_type == "commonsense_reasoning"


def test_winogrande_splits():
    # test split labels are withheld
    assert WinoGrandeAdapter().splits == ["train", "validation"]


def test_winogrande_is_dataset_adapter():
    assert isinstance(WinoGrandeAdapter(), DatasetAdapter)


# ---------------------------------------------------------------------------
# WinoGrande adapter — parse_example tests
# ---------------------------------------------------------------------------


def test_winogrande_parse_example_answer_1():
    """Answer '1' should map to letter 'A' (option1)."""
    row = {
        "sentence": "Sarah was nicer than Emma because _ was always kind.",
        "option1": "Sarah",
        "option2": "Emma",
        "answer": "1",
    }
    adapter = WinoGrandeAdapter()
    example = adapter.parse_example(row, DATASET_ID, "train")

    assert isinstance(example, Example)
    assert example.dataset_id == DATASET_ID
    assert example.question == "Sarah was nicer than Emma because _ was always kind."
    assert example.answer == "A"
    assert example.choices == ["A: Sarah", "B: Emma"]
    assert example.example_metadata["split"] == "train"


def test_winogrande_parse_example_answer_2():
    """Answer '2' should map to letter 'B' (option2)."""
    row = {
        "sentence": "Mark thanked Chris because _ gave great advice.",
        "option1": "Mark",
        "option2": "Chris",
        "answer": "2",
    }
    adapter = WinoGrandeAdapter()
    example = adapter.parse_example(row, DATASET_ID, "validation")

    assert example.answer == "B"
    assert example.choices == ["A: Mark", "B: Chris"]
    assert example.example_metadata["split"] == "validation"


def test_winogrande_parse_example_choices_format():
    """Choices must be formatted as 'A: option1' and 'B: option2'."""
    row = {
        "sentence": "The dog chased the cat until _ got tired.",
        "option1": "the dog",
        "option2": "the cat",
        "answer": "1",
    }
    example = WinoGrandeAdapter().parse_example(row, DATASET_ID, "train")

    assert example.choices[0] == "A: the dog"
    assert example.choices[1] == "B: the cat"


def test_winogrande_parse_example_unknown_answer():
    """An answer value other than '1' or '2' should produce None."""
    row = {
        "sentence": "They ran toward _ quickly.",
        "option1": "Alice",
        "option2": "Bob",
        "answer": "",
    }
    example = WinoGrandeAdapter().parse_example(row, DATASET_ID, "train")

    assert example.answer is None


def test_winogrande_parse_example_missing_fields():
    """parse_example should handle missing fields gracefully."""
    example = WinoGrandeAdapter().parse_example({}, DATASET_ID, "train")

    assert example.question == ""
    assert example.answer is None
    assert example.choices == ["A: ", "B: "]
    assert example.example_metadata["split"] == "train"


# ---------------------------------------------------------------------------
# PIQA adapter — property tests
# ---------------------------------------------------------------------------


def test_piqa_name():
    assert PIQAAdapter().name == "PIQA"


def test_piqa_source():
    assert PIQAAdapter().source == "HuggingFace:ybisk/piqa"


def test_piqa_hf_dataset_id():
    assert PIQAAdapter().hf_dataset_id == "ybisk/piqa"


def test_piqa_hf_config():
    assert PIQAAdapter().hf_config is None


def test_piqa_license():
    assert PIQAAdapter().license == "AFL-3.0"


def test_piqa_task_type():
    assert PIQAAdapter().task_type == "physical_intuition"


def test_piqa_splits():
    # test labels are -1 (withheld)
    assert PIQAAdapter().splits == ["train", "validation"]


def test_piqa_is_dataset_adapter():
    assert isinstance(PIQAAdapter(), DatasetAdapter)


# ---------------------------------------------------------------------------
# PIQA adapter — parse_example tests
# ---------------------------------------------------------------------------


def test_piqa_parse_example_label_0():
    """Label 0 should map to letter 'A' (sol1)."""
    row = {
        "goal": "To make ice cubes, you should",
        "sol1": "fill a tray with water and put it in the freezer",
        "sol2": "fill a tray with water and put it in the oven",
        "label": 0,
    }
    adapter = PIQAAdapter()
    example = adapter.parse_example(row, DATASET_ID, "train")

    assert isinstance(example, Example)
    assert example.dataset_id == DATASET_ID
    assert example.question == "To make ice cubes, you should"
    assert example.answer == "A"
    assert example.choices == [
        "A: fill a tray with water and put it in the freezer",
        "B: fill a tray with water and put it in the oven",
    ]
    assert example.example_metadata["split"] == "train"


def test_piqa_parse_example_label_1():
    """Label 1 should map to letter 'B' (sol2)."""
    row = {
        "goal": "To dry wet clothes faster, you should",
        "sol1": "leave them in a cold damp room",
        "sol2": "hang them outside on a sunny breezy day",
        "label": 1,
    }
    adapter = PIQAAdapter()
    example = adapter.parse_example(row, DATASET_ID, "validation")

    assert example.answer == "B"
    assert example.choices == [
        "A: leave them in a cold damp room",
        "B: hang them outside on a sunny breezy day",
    ]
    assert example.example_metadata["split"] == "validation"


def test_piqa_parse_example_choices_format():
    """Choices must be formatted as 'A: sol1' and 'B: sol2'."""
    row = {
        "goal": "To sharpen a pencil",
        "sol1": "use a pencil sharpener",
        "sol2": "use a hammer",
        "label": 0,
    }
    example = PIQAAdapter().parse_example(row, DATASET_ID, "train")

    assert example.choices[0] == "A: use a pencil sharpener"
    assert example.choices[1] == "B: use a hammer"


def test_piqa_parse_example_label_none():
    """None label (e.g. test split) should produce answer None."""
    row = {
        "goal": "To open a can",
        "sol1": "use a can opener",
        "sol2": "use scissors",
        "label": None,
    }
    example = PIQAAdapter().parse_example(row, DATASET_ID, "train")

    assert example.answer is None


def test_piqa_parse_example_label_minus_one():
    """Label -1 (withheld test labels) should produce answer None."""
    row = {
        "goal": "To boil water",
        "sol1": "put it on the stove",
        "sol2": "put it in the fridge",
        "label": -1,
    }
    example = PIQAAdapter().parse_example(row, DATASET_ID, "test")

    assert example.answer is None


def test_piqa_parse_example_missing_fields():
    """parse_example should handle missing fields gracefully."""
    example = PIQAAdapter().parse_example({}, DATASET_ID, "train")

    assert example.question == ""
    assert example.answer is None
    assert example.choices == ["A: ", "B: "]
    assert example.example_metadata["split"] == "train"


# ---------------------------------------------------------------------------
# MBPP adapter — property tests
# ---------------------------------------------------------------------------


def test_mbpp_name():
    assert MBPPAdapter().name == "MBPP"


def test_mbpp_source():
    assert MBPPAdapter().source == "HuggingFace:google-research-datasets/mbpp"


def test_mbpp_hf_dataset_id():
    assert MBPPAdapter().hf_dataset_id == "google-research-datasets/mbpp"


def test_mbpp_hf_config():
    assert MBPPAdapter().hf_config == "full"


def test_mbpp_license():
    assert MBPPAdapter().license == "CC-BY-4.0"


def test_mbpp_task_type():
    assert MBPPAdapter().task_type == "code_generation"


def test_mbpp_splits():
    assert MBPPAdapter().splits == ["train", "validation", "test"]


def test_mbpp_is_dataset_adapter():
    assert isinstance(MBPPAdapter(), DatasetAdapter)


# ---------------------------------------------------------------------------
# MBPP adapter — parse_example tests
# ---------------------------------------------------------------------------


def test_mbpp_parse_example():
    """Full parse_example with all fields present."""
    row = {
        "task_id": 11,
        "text": "Write a Python function to add two numbers.",
        "code": "def add(a, b):\n    return a + b",
        "test_list": [
            "assert add(1, 2) == 3",
            "assert add(0, 0) == 0",
            "assert add(-1, 1) == 0",
        ],
        "test_setup_code": "",
        "challenge_test_list": ["assert add(100, 200) == 300"],
    }
    adapter = MBPPAdapter()
    example = adapter.parse_example(row, DATASET_ID, "train")

    assert isinstance(example, Example)
    assert example.dataset_id == DATASET_ID
    assert example.question == "Write a Python function to add two numbers."
    assert example.answer == "def add(a, b):\n    return a + b"
    assert example.choices is None
    assert example.example_metadata["task_id"] == 11
    assert example.example_metadata["num_tests"] == 3
    assert example.example_metadata["has_challenge_tests"] is True
    assert example.example_metadata["split"] == "train"


def test_mbpp_parse_example_no_challenge_tests():
    """has_challenge_tests should be False when challenge_test_list is empty."""
    row = {
        "task_id": 42,
        "text": "Write a function that squares a number.",
        "code": "def square(n):\n    return n * n",
        "test_list": ["assert square(3) == 9"],
        "test_setup_code": "",
        "challenge_test_list": [],
    }
    example = MBPPAdapter().parse_example(row, DATASET_ID, "test")

    assert example.example_metadata["num_tests"] == 1
    assert example.example_metadata["has_challenge_tests"] is False


def test_mbpp_parse_example_num_tests_count():
    """num_tests should equal the length of test_list."""
    row = {
        "task_id": 7,
        "text": "Sum a list.",
        "code": "def sum_list(lst):\n    return sum(lst)",
        "test_list": ["assert sum_list([1,2]) == 3", "assert sum_list([]) == 0"],
        "test_setup_code": "",
        "challenge_test_list": [],
    }
    example = MBPPAdapter().parse_example(row, DATASET_ID, "validation")

    assert example.example_metadata["num_tests"] == 2


def test_mbpp_parse_example_missing_code():
    """When code is missing the answer should be None."""
    row = {
        "task_id": 99,
        "text": "Some problem",
        "test_list": [],
        "test_setup_code": "",
        "challenge_test_list": [],
    }
    example = MBPPAdapter().parse_example(row, DATASET_ID, "train")

    assert example.answer is None


def test_mbpp_parse_example_missing_fields():
    """parse_example should handle completely empty row gracefully."""
    example = MBPPAdapter().parse_example({}, DATASET_ID, "train")

    assert example.question == ""
    assert example.answer is None
    assert example.choices is None
    assert example.example_metadata["task_id"] == ""
    assert example.example_metadata["num_tests"] == 0
    assert example.example_metadata["has_challenge_tests"] is False


# ---------------------------------------------------------------------------
# BoolQ adapter — property tests
# ---------------------------------------------------------------------------


def test_boolq_name():
    assert BoolQAdapter().name == "BoolQ"


def test_boolq_source():
    assert BoolQAdapter().source == "HuggingFace:google/boolq"


def test_boolq_hf_dataset_id():
    assert BoolQAdapter().hf_dataset_id == "google/boolq"


def test_boolq_hf_config():
    assert BoolQAdapter().hf_config is None


def test_boolq_license():
    assert BoolQAdapter().license == "CC-BY-SA-3.0"


def test_boolq_task_type():
    assert BoolQAdapter().task_type == "reading_comprehension"


def test_boolq_splits():
    assert BoolQAdapter().splits == ["train", "validation"]


def test_boolq_is_dataset_adapter():
    assert isinstance(BoolQAdapter(), DatasetAdapter)


# ---------------------------------------------------------------------------
# BoolQ adapter — parse_example tests
# ---------------------------------------------------------------------------


def test_boolq_parse_example_true():
    """Boolean True answer should map to 'Yes'."""
    row = {
        "question": "is the sky blue",
        "answer": True,
        "passage": (
            "The sky appears blue during the day due to Rayleigh scattering of sunlight "
            "by the atmosphere."
        ),
    }
    adapter = BoolQAdapter()
    example = adapter.parse_example(row, DATASET_ID, "train")

    assert isinstance(example, Example)
    assert example.dataset_id == DATASET_ID
    assert example.question == "is the sky blue"
    assert example.answer == "Yes"
    assert example.choices == ["A: Yes", "B: No"]
    assert example.example_metadata["split"] == "train"


def test_boolq_parse_example_false():
    """Boolean False answer should map to 'No'."""
    row = {
        "question": "is the moon made of cheese",
        "answer": False,
        "passage": "The Moon is a rocky, airless world covered in craters.",
    }
    adapter = BoolQAdapter()
    example = adapter.parse_example(row, DATASET_ID, "validation")

    assert example.answer == "No"
    assert example.example_metadata["split"] == "validation"


def test_boolq_choices_always_yes_no():
    """Choices must always be ['A: Yes', 'B: No'] regardless of answer."""
    row = {"question": "does water freeze at 0C", "answer": True, "passage": "Water freezes."}
    example = BoolQAdapter().parse_example(row, DATASET_ID, "train")

    assert example.choices == ["A: Yes", "B: No"]


def test_boolq_parse_example_passage_truncated():
    """Passage excerpt in metadata must be truncated to 500 characters."""
    long_passage = "A" * 1000
    row = {
        "question": "is this long",
        "answer": True,
        "passage": long_passage,
    }
    example = BoolQAdapter().parse_example(row, DATASET_ID, "train")

    assert len(example.example_metadata["passage"]) == 500


def test_boolq_parse_example_short_passage_not_truncated():
    """Short passages should be stored in full."""
    short_passage = "Water is wet."
    row = {
        "question": "is water wet",
        "answer": True,
        "passage": short_passage,
    }
    example = BoolQAdapter().parse_example(row, DATASET_ID, "train")

    assert example.example_metadata["passage"] == short_passage


def test_boolq_parse_example_none_answer():
    """None answer should produce answer=None (not crash)."""
    row = {
        "question": "some question",
        "answer": None,
        "passage": "some passage",
    }
    example = BoolQAdapter().parse_example(row, DATASET_ID, "train")

    assert example.answer is None


def test_boolq_parse_example_missing_fields():
    """parse_example should handle completely empty row gracefully."""
    example = BoolQAdapter().parse_example({}, DATASET_ID, "train")

    assert example.question == ""
    assert example.answer is None
    assert example.choices == ["A: Yes", "B: No"]
    assert example.example_metadata["passage"] == ""
    assert example.example_metadata["split"] == "train"


# ---------------------------------------------------------------------------
# Registry tests — batch 2 additions
# ---------------------------------------------------------------------------


def test_registry_contains_batch2_adapters():
    """All 4 batch-2 adapters must be present in the registry."""
    for key in ("winogrande", "piqa", "mbpp", "boolq"):
        assert key in ADAPTER_REGISTRY, f"'{key}' not found in ADAPTER_REGISTRY"


def test_registry_total_adapter_count():
    """Registry should now contain 10 adapters (6 original + 4 new)."""
    assert len(ADAPTER_REGISTRY) == 10


def test_registry_winogrande_class():
    assert ADAPTER_REGISTRY["winogrande"] is WinoGrandeAdapter


def test_registry_piqa_class():
    assert ADAPTER_REGISTRY["piqa"] is PIQAAdapter


def test_registry_mbpp_class():
    assert ADAPTER_REGISTRY["mbpp"] is MBPPAdapter


def test_registry_boolq_class():
    assert ADAPTER_REGISTRY["boolq"] is BoolQAdapter


def test_registry_batch2_adapters_are_subclasses():
    """Every batch-2 adapter must extend DatasetAdapter."""
    for key in ("winogrande", "piqa", "mbpp", "boolq"):
        cls = ADAPTER_REGISTRY[key]
        assert issubclass(cls, DatasetAdapter), f"'{key}' adapter does not extend DatasetAdapter"


def test_registry_batch2_adapters_instantiable():
    """Every batch-2 adapter must be instantiable with no arguments."""
    for key in ("winogrande", "piqa", "mbpp", "boolq"):
        instance = ADAPTER_REGISTRY[key]()
        assert isinstance(instance, DatasetAdapter), f"'{key}' adapter failed to instantiate"


@pytest.mark.parametrize("key", ["winogrande", "piqa", "mbpp", "boolq"])
def test_registry_batch2_adapter_has_description(key):
    """All new adapters should have a non-empty description."""
    adapter = ADAPTER_REGISTRY[key]()
    assert isinstance(adapter.description, str) and len(adapter.description) > 0
