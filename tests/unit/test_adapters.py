"""Unit tests for dataset ingestion adapters and the adapter registry."""

from cherry_evals.ingestion.arc import ARCAdapter, _format_arc_choices
from cherry_evals.ingestion.base import DatasetAdapter
from cherry_evals.ingestion.gsm8k import GSM8KAdapter, _extract_final_answer
from cherry_evals.ingestion.hellaswag import HellaSwagAdapter
from cherry_evals.ingestion.humaneval import HumanEvalAdapter
from cherry_evals.ingestion.mmlu import MMLUAdapter
from cherry_evals.ingestion.registry import ADAPTER_REGISTRY
from cherry_evals.ingestion.truthfulqa import TruthfulQAAdapter, _mc1_correct_letter
from db.postgres.models import Example

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DATASET_ID = 1


# ---------------------------------------------------------------------------
# MMLU adapter
# ---------------------------------------------------------------------------


def test_mmlu_name():
    assert MMLUAdapter().name == "MMLU"


def test_mmlu_source():
    assert MMLUAdapter().source == "HuggingFace:cais/mmlu"


def test_mmlu_hf_dataset_id():
    assert MMLUAdapter().hf_dataset_id == "cais/mmlu"


def test_mmlu_hf_config():
    assert MMLUAdapter().hf_config == "all"


def test_mmlu_license():
    assert MMLUAdapter().license == "MIT"


def test_mmlu_task_type():
    assert MMLUAdapter().task_type == "multiple_choice"


def test_mmlu_splits():
    assert MMLUAdapter().splits == ["test", "validation", "dev"]


def test_mmlu_is_dataset_adapter():
    assert isinstance(MMLUAdapter(), DatasetAdapter)


def test_mmlu_parse_example():
    row = {
        "question": "What is the primary function of the mitochondria?",
        "choices": ["Protein synthesis", "Energy production", "DNA replication", "Cell division"],
        "answer": 1,
        "subject": "anatomy",
    }
    adapter = MMLUAdapter()
    example = adapter.parse_example(row, DATASET_ID, "test")

    assert isinstance(example, Example)
    assert example.dataset_id == DATASET_ID
    assert example.question == "What is the primary function of the mitochondria?"
    assert example.answer == "B"
    assert example.choices == [
        "A: Protein synthesis",
        "B: Energy production",
        "C: DNA replication",
        "D: Cell division",
    ]
    assert example.example_metadata["subject"] == "anatomy"
    assert example.example_metadata["split"] == "test"
    assert example.example_metadata["answer_index"] == 1
    assert example.example_metadata["num_choices"] == 4


def test_mmlu_parse_example_answer_zero():
    """Answer index 0 should map to letter 'A'."""
    row = {
        "question": "What is 1+1?",
        "choices": ["2", "3", "4", "5"],
        "answer": 0,
        "subject": "math",
    }
    example = MMLUAdapter().parse_example(row, DATASET_ID, "dev")

    assert example.answer == "A"


def test_mmlu_parse_example_formats_choices():
    """Choices should be formatted as 'A: text', 'B: text', etc."""
    row = {
        "question": "Which planet is closest to the sun?",
        "choices": ["Venus", "Mercury", "Earth", "Mars"],
        "answer": 1,
        "subject": "astronomy",
    }
    example = MMLUAdapter().parse_example(row, DATASET_ID, "test")

    assert example.choices[0] == "A: Venus"
    assert example.choices[1] == "B: Mercury"


def test_mmlu_parse_example_missing_fields():
    """parse_example should handle missing fields gracefully."""
    example = MMLUAdapter().parse_example({}, DATASET_ID, "test")

    assert example.question == ""
    assert example.answer is None  # out-of-range index → None
    assert example.choices == []
    assert example.example_metadata["subject"] == "unknown"


# ---------------------------------------------------------------------------
# HumanEval adapter
# ---------------------------------------------------------------------------


def test_humaneval_name():
    assert HumanEvalAdapter().name == "HumanEval"


def test_humaneval_source():
    assert HumanEvalAdapter().source == "HuggingFace:openai/openai_humaneval"


def test_humaneval_hf_dataset_id():
    assert HumanEvalAdapter().hf_dataset_id == "openai/openai_humaneval"


def test_humaneval_hf_config():
    assert HumanEvalAdapter().hf_config is None


def test_humaneval_license():
    assert HumanEvalAdapter().license == "MIT"


def test_humaneval_task_type():
    assert HumanEvalAdapter().task_type == "code_generation"


def test_humaneval_splits():
    assert HumanEvalAdapter().splits == ["test"]


def test_humaneval_is_dataset_adapter():
    assert isinstance(HumanEvalAdapter(), DatasetAdapter)


def test_humaneval_parse_example():
    row = {
        "task_id": "HumanEval/0",
        "prompt": 'def add(a, b):\n    """Add two numbers"""\n',
        "canonical_solution": "    return a + b\n",
        "test": "assert add(1,2)==3",
        "entry_point": "add",
    }
    adapter = HumanEvalAdapter()
    example = adapter.parse_example(row, DATASET_ID, "test")

    assert isinstance(example, Example)
    assert example.dataset_id == DATASET_ID
    assert example.question == 'def add(a, b):\n    """Add two numbers"""\n'
    assert example.answer == "    return a + b\n"
    assert example.choices is None
    assert example.example_metadata["task_id"] == "HumanEval/0"
    assert example.example_metadata["entry_point"] == "add"
    assert example.example_metadata["has_test"] is True
    assert example.example_metadata["split"] == "test"


def test_humaneval_parse_example_missing_fields():
    """parse_example should handle missing fields gracefully."""
    example = HumanEvalAdapter().parse_example({}, DATASET_ID, "test")

    assert example.question == ""
    assert example.answer is None
    assert example.choices is None
    assert example.example_metadata["task_id"] == ""
    assert example.example_metadata["entry_point"] == ""


# ---------------------------------------------------------------------------
# GSM8K adapter
# ---------------------------------------------------------------------------


def test_gsm8k_name():
    assert GSM8KAdapter().name == "GSM8K"


def test_gsm8k_source():
    assert GSM8KAdapter().source == "HuggingFace:openai/gsm8k"


def test_gsm8k_hf_dataset_id():
    assert GSM8KAdapter().hf_dataset_id == "openai/gsm8k"


def test_gsm8k_hf_config():
    assert GSM8KAdapter().hf_config == "main"


def test_gsm8k_license():
    assert GSM8KAdapter().license == "MIT"


def test_gsm8k_task_type():
    assert GSM8KAdapter().task_type == "math_reasoning"


def test_gsm8k_splits():
    assert GSM8KAdapter().splits == ["train", "test"]


def test_gsm8k_is_dataset_adapter():
    assert isinstance(GSM8KAdapter(), DatasetAdapter)


def test_gsm8k_parse_example():
    row = {
        "question": "If John has 5 apples and gives 2 to Mary, how many does he have?",
        "answer": "John starts with 5 apples. He gives 2 away. 5 - 2 = 3. #### 3",
    }
    adapter = GSM8KAdapter()
    example = adapter.parse_example(row, DATASET_ID, "train")

    assert isinstance(example, Example)
    assert example.dataset_id == DATASET_ID
    assert example.question == "If John has 5 apples and gives 2 to Mary, how many does he have?"
    assert example.answer == "John starts with 5 apples. He gives 2 away. 5 - 2 = 3. #### 3"
    assert example.choices is None
    assert example.example_metadata["split"] == "train"
    assert example.example_metadata["final_answer"] == "3"


def test_gsm8k_extracts_final_answer():
    """_extract_final_answer should parse the number after ####."""
    assert _extract_final_answer("Some reasoning steps. #### 42") == "42"


def test_gsm8k_extracts_final_answer_with_thousands_separator():
    """Commas used as thousands separators should be stripped."""
    assert _extract_final_answer("Result: #### 1,234") == "1234"


def test_gsm8k_extracts_final_answer_decimal():
    """Decimal answers should be returned as-is."""
    assert _extract_final_answer("#### 3.14") == "3.14"


def test_gsm8k_extracts_final_answer_no_separator():
    """When no #### separator is present, return None."""
    assert _extract_final_answer("The answer is 7.") is None


def test_gsm8k_parse_example_no_separator():
    """Metadata final_answer should be None when #### is absent."""
    row = {
        "question": "What is 2 + 2?",
        "answer": "The answer is 4.",
    }
    example = GSM8KAdapter().parse_example(row, DATASET_ID, "test")

    assert example.example_metadata["final_answer"] is None
    # Full answer text is still stored verbatim
    assert example.answer == "The answer is 4."


# ---------------------------------------------------------------------------
# HellaSwag adapter
# ---------------------------------------------------------------------------


def test_hellaswag_name():
    assert HellaSwagAdapter().name == "HellaSwag"


def test_hellaswag_source():
    assert HellaSwagAdapter().source == "HuggingFace:Rowan/hellaswag"


def test_hellaswag_hf_dataset_id():
    assert HellaSwagAdapter().hf_dataset_id == "Rowan/hellaswag"


def test_hellaswag_hf_config():
    assert HellaSwagAdapter().hf_config is None


def test_hellaswag_license():
    assert HellaSwagAdapter().license == "MIT"


def test_hellaswag_task_type():
    assert HellaSwagAdapter().task_type == "commonsense_reasoning"


def test_hellaswag_splits():
    # test split is withheld for the leaderboard; only train + validation are ingested
    assert HellaSwagAdapter().splits == ["train", "validation"]


def test_hellaswag_is_dataset_adapter():
    assert isinstance(HellaSwagAdapter(), DatasetAdapter)


def test_hellaswag_parse_example():
    row = {
        "ind": 1,
        "activity_label": "cooking",
        "ctx_a": "A chef",
        "ctx_b": "picks up a knife",
        "ctx": "A chef picks up a knife",
        "endings": [
            "and cuts vegetables",
            "and plays piano",
            "and reads a book",
            "and goes swimming",
        ],
        "source_id": "test",
        "split": "train",
        "split_type": "indomain",
        "label": "0",
    }
    adapter = HellaSwagAdapter()
    example = adapter.parse_example(row, DATASET_ID, "train")

    assert isinstance(example, Example)
    assert example.dataset_id == DATASET_ID
    assert example.question == "A chef picks up a knife"
    assert example.answer == "A"
    assert example.choices == [
        "A: and cuts vegetables",
        "B: and plays piano",
        "C: and reads a book",
        "D: and goes swimming",
    ]
    assert example.example_metadata["activity_label"] == "cooking"
    assert example.example_metadata["split"] == "train"
    assert example.example_metadata["answer_index"] == 0


def test_hellaswag_parse_example_label_as_string_index():
    """Label stored as string integer should resolve to correct letter."""
    row = {
        "ctx": "She opened the door",
        "endings": ["slowly", "quickly", "carefully", "loudly"],
        "label": "2",
        "activity_label": "entering",
    }
    example = HellaSwagAdapter().parse_example(row, DATASET_ID, "validation")

    assert example.answer == "C"
    assert example.example_metadata["answer_index"] == 2


def test_hellaswag_parse_example_invalid_label():
    """A non-numeric label should fall back to index 0 (letter 'A')."""
    row = {
        "ctx": "The athlete ran",
        "endings": ["fast", "slow", "backwards", "sideways"],
        "label": "invalid",
        "activity_label": "sports",
    }
    example = HellaSwagAdapter().parse_example(row, DATASET_ID, "train")

    assert example.answer == "A"
    assert example.example_metadata["answer_index"] == 0


def test_hellaswag_parse_example_empty_label():
    """An empty string label should fall back gracefully."""
    row = {
        "ctx": "He cooked dinner",
        "endings": ["well", "badly", "quickly", "slowly"],
        "label": "",
        "activity_label": "cooking",
    }
    example = HellaSwagAdapter().parse_example(row, DATASET_ID, "train")

    assert example.answer == "A"
    assert example.example_metadata["answer_index"] == 0


# ---------------------------------------------------------------------------
# TruthfulQA adapter
# ---------------------------------------------------------------------------


def test_truthfulqa_name():
    assert TruthfulQAAdapter().name == "TruthfulQA"


def test_truthfulqa_source():
    assert TruthfulQAAdapter().source == "HuggingFace:truthfulqa/truthful_qa"


def test_truthfulqa_hf_dataset_id():
    assert TruthfulQAAdapter().hf_dataset_id == "truthfulqa/truthful_qa"


def test_truthfulqa_hf_config():
    assert TruthfulQAAdapter().hf_config == "multiple_choice"


def test_truthfulqa_license():
    assert TruthfulQAAdapter().license == "Apache-2.0"


def test_truthfulqa_task_type():
    assert TruthfulQAAdapter().task_type == "truthfulness"


def test_truthfulqa_splits():
    assert TruthfulQAAdapter().splits == ["validation"]


def test_truthfulqa_is_dataset_adapter():
    assert isinstance(TruthfulQAAdapter(), DatasetAdapter)


def test_truthfulqa_parse_example():
    row = {
        "question": "Is the Earth flat?",
        "mc1_targets": {
            "choices": [
                "No, the Earth is roughly spherical",
                "Yes, the Earth is flat",
                "Yes, obviously",
            ],
            "labels": [1, 0, 0],
        },
    }
    adapter = TruthfulQAAdapter()
    example = adapter.parse_example(row, DATASET_ID, "validation")

    assert isinstance(example, Example)
    assert example.dataset_id == DATASET_ID
    assert example.question == "Is the Earth flat?"
    # First choice (index 0) has label 1, so correct letter is "A"
    assert example.answer == "A"
    assert example.choices == [
        "A: No, the Earth is roughly spherical",
        "B: Yes, the Earth is flat",
        "C: Yes, obviously",
    ]
    assert example.example_metadata["split"] == "validation"


def test_truthfulqa_correct_letter_first_position():
    mc1 = {"choices": ["right", "wrong", "wrong"], "labels": [1, 0, 0]}
    assert _mc1_correct_letter(mc1) == "A"


def test_truthfulqa_correct_letter_middle_position():
    mc1 = {"choices": ["wrong", "right", "wrong"], "labels": [0, 1, 0]}
    assert _mc1_correct_letter(mc1) == "B"


def test_truthfulqa_correct_letter_last_position():
    mc1 = {"choices": ["wrong", "wrong", "right"], "labels": [0, 0, 1]}
    assert _mc1_correct_letter(mc1) == "C"


def test_truthfulqa_parse_example_no_correct_answer():
    """When no label is 1 in mc1_targets, answer should be None."""
    row = {
        "question": "Which way is up?",
        "mc1_targets": {
            "choices": ["North", "South"],
            "labels": [0, 0],
        },
    }
    example = TruthfulQAAdapter().parse_example(row, DATASET_ID, "validation")

    assert example.answer is None


def test_truthfulqa_mc1_correct_letter_no_correct():
    """_mc1_correct_letter returns None when all labels are 0."""
    mc1 = {"choices": ["a", "b"], "labels": [0, 0]}
    assert _mc1_correct_letter(mc1) is None


def test_truthfulqa_mc1_correct_letter_empty():
    """_mc1_correct_letter returns None for empty mc1_targets."""
    assert _mc1_correct_letter({}) is None


# ---------------------------------------------------------------------------
# ARC adapter
# ---------------------------------------------------------------------------


def test_arc_name():
    assert ARCAdapter().name == "ARC"


def test_arc_source():
    assert ARCAdapter().source == "HuggingFace:allenai/ai2_arc"


def test_arc_hf_dataset_id():
    assert ARCAdapter().hf_dataset_id == "allenai/ai2_arc"


def test_arc_hf_config():
    assert ARCAdapter().hf_config == "ARC-Challenge"


def test_arc_license():
    assert ARCAdapter().license == "CC-BY-SA-4.0"


def test_arc_task_type():
    assert ARCAdapter().task_type == "science_qa"


def test_arc_splits():
    assert ARCAdapter().splits == ["train", "validation", "test"]


def test_arc_is_dataset_adapter():
    assert isinstance(ARCAdapter(), DatasetAdapter)


def test_arc_parse_example():
    row = {
        "id": "Q123",
        "question": "What causes seasons on Earth?",
        "choices": {
            "text": ["Earth's tilt", "Distance from sun", "Moon phases", "Wind patterns"],
            "label": ["A", "B", "C", "D"],
        },
        "answerKey": "A",
    }
    adapter = ARCAdapter()
    example = adapter.parse_example(row, DATASET_ID, "test")

    assert isinstance(example, Example)
    assert example.dataset_id == DATASET_ID
    assert example.question == "What causes seasons on Earth?"
    assert example.answer == "A"
    assert example.choices == [
        "A: Earth's tilt",
        "B: Distance from sun",
        "C: Moon phases",
        "D: Wind patterns",
    ]
    assert example.example_metadata["question_id"] == "Q123"
    assert example.example_metadata["split"] == "test"
    assert example.example_metadata["difficulty"] == "challenge"


def test_arc_parse_example_answer_key_b():
    """answerKey 'B' should be stored verbatim."""
    row = {
        "id": "Q999",
        "question": "What is H2O?",
        "choices": {
            "text": ["Carbon", "Water", "Salt", "Gold"],
            "label": ["A", "B", "C", "D"],
        },
        "answerKey": "B",
    }
    example = ARCAdapter().parse_example(row, DATASET_ID, "train")

    assert example.answer == "B"


def test_arc_parse_example_three_choices():
    """ARC sometimes has 3 choices; adapter should handle variable counts."""
    row = {
        "id": "Q456",
        "question": "What is the boiling point of water?",
        "choices": {
            "text": ["50°C", "100°C", "150°C"],
            "label": ["A", "B", "C"],
        },
        "answerKey": "B",
    }
    example = ARCAdapter().parse_example(row, DATASET_ID, "test")

    assert len(example.choices) == 3
    assert example.choices == ["A: 50°C", "B: 100°C", "C: 150°C"]
    assert example.answer == "B"


def test_arc_format_arc_choices():
    """_format_arc_choices should produce 'label: text' strings."""
    choices = {
        "text": ["Red", "Green", "Blue"],
        "label": ["A", "B", "C"],
    }
    result = _format_arc_choices(choices)

    assert result == ["A: Red", "B: Green", "C: Blue"]


def test_arc_format_arc_choices_empty():
    """_format_arc_choices should return an empty list for empty input."""
    assert _format_arc_choices({}) == []
    assert _format_arc_choices({"text": [], "label": []}) == []


def test_arc_parse_example_missing_fields():
    """parse_example should handle missing fields gracefully."""
    example = ARCAdapter().parse_example({}, DATASET_ID, "test")

    assert example.question == ""
    assert example.answer is None
    assert example.choices == []
    assert example.example_metadata["question_id"] == ""


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------


def test_registry_contains_all_adapters():
    """All 6 expected adapters must be registered."""
    expected_keys = {"mmlu", "humaneval", "gsm8k", "hellaswag", "truthfulqa", "arc"}
    assert set(ADAPTER_REGISTRY.keys()) == expected_keys


def test_registry_adapter_count():
    assert len(ADAPTER_REGISTRY) == 6


def test_registry_mmlu_class():
    assert ADAPTER_REGISTRY["mmlu"] is MMLUAdapter


def test_registry_humaneval_class():
    assert ADAPTER_REGISTRY["humaneval"] is HumanEvalAdapter


def test_registry_gsm8k_class():
    assert ADAPTER_REGISTRY["gsm8k"] is GSM8KAdapter


def test_registry_hellaswag_class():
    assert ADAPTER_REGISTRY["hellaswag"] is HellaSwagAdapter


def test_registry_truthfulqa_class():
    assert ADAPTER_REGISTRY["truthfulqa"] is TruthfulQAAdapter


def test_registry_arc_class():
    assert ADAPTER_REGISTRY["arc"] is ARCAdapter


def test_registry_all_values_are_dataset_adapter_subclasses():
    """Every value in the registry must be a concrete DatasetAdapter subclass."""
    for key, cls in ADAPTER_REGISTRY.items():
        assert issubclass(cls, DatasetAdapter), f"{key!r} adapter does not extend DatasetAdapter"


def test_registry_all_adapters_instantiable():
    """Every registered adapter must be instantiable with no arguments."""
    for key, cls in ADAPTER_REGISTRY.items():
        instance = cls()
        assert isinstance(instance, DatasetAdapter), f"{key!r} adapter failed to instantiate"
