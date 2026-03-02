"""Unit tests for export format converters."""

import csv
import io
import json
from types import SimpleNamespace

import pytest

from core.export.formats import to_csv, to_json, to_jsonl


def _make_example(id, dataset_id, question, answer, choices=None, example_metadata=None):
    """Create a mock example object for testing."""
    return SimpleNamespace(
        id=id,
        dataset_id=dataset_id,
        question=question,
        answer=answer,
        choices=choices,
        example_metadata=example_metadata,
    )


@pytest.fixture
def sample_examples():
    return [
        _make_example(
            1,
            10,
            "What is 2+2?",
            "4",
            choices=["3", "4", "5"],
            example_metadata={"subject": "math"},
        ),
        _make_example(2, 10, "Capital of France?", "Paris"),
        _make_example(3, 20, "def hello():", "print('hi')", example_metadata={"lang": "python"}),
    ]


@pytest.fixture
def dataset_names():
    return {10: "MMLU", 20: "HumanEval"}


class TestToJson:
    def test_basic_export(self, sample_examples, dataset_names):
        result = to_json(sample_examples, dataset_names)
        data = json.loads(result)

        assert len(data) == 3
        assert data[0]["id"] == 1
        assert data[0]["question"] == "What is 2+2?"
        assert data[0]["answer"] == "4"
        assert data[0]["choices"] == ["3", "4", "5"]
        assert data[0]["dataset_name"] == "MMLU"
        assert data[0]["metadata"] == {"subject": "math"}

    def test_without_dataset_names(self, sample_examples):
        result = to_json(sample_examples)
        data = json.loads(result)

        assert "dataset_name" not in data[0]

    def test_empty_list(self):
        result = to_json([])
        assert json.loads(result) == []

    def test_null_fields(self):
        ex = _make_example(1, 1, "Q?", None, choices=None, example_metadata=None)
        result = to_json([ex])
        data = json.loads(result)

        assert data[0]["answer"] is None
        assert data[0]["choices"] is None
        assert "metadata" not in data[0]


class TestToJsonl:
    def test_basic_export(self, sample_examples, dataset_names):
        result = to_jsonl(sample_examples, dataset_names)
        lines = result.strip().split("\n")

        assert len(lines) == 3
        first = json.loads(lines[0])
        assert first["id"] == 1
        assert first["dataset_name"] == "MMLU"

    def test_each_line_is_valid_json(self, sample_examples):
        result = to_jsonl(sample_examples)
        for line in result.strip().split("\n"):
            json.loads(line)  # Should not raise

    def test_empty_list(self):
        result = to_jsonl([])
        assert result == ""


class TestToCsv:
    def test_basic_export(self, sample_examples, dataset_names):
        result = to_csv(sample_examples, dataset_names)
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) == 3
        assert rows[0]["id"] == "1"
        assert rows[0]["question"] == "What is 2+2?"
        assert rows[0]["dataset_name"] == "MMLU"
        # Choices should be JSON-serialized
        assert json.loads(rows[0]["choices"]) == ["3", "4", "5"]

    def test_csv_header(self, sample_examples):
        result = to_csv(sample_examples)
        first_line = result.split("\n")[0]
        assert "id" in first_line
        assert "question" in first_line
        assert "answer" in first_line

    def test_empty_list(self):
        result = to_csv([])
        # Should still have header
        assert "id" in result
        reader = csv.DictReader(io.StringIO(result))
        assert list(reader) == []
