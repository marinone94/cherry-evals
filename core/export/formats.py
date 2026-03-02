"""Export collection examples to various file formats."""

import csv
import io
import json


def _example_to_dict(example, dataset_name: str | None = None) -> dict:
    """Convert an Example ORM object to a flat export dictionary."""
    d = {
        "id": example.id,
        "dataset_id": example.dataset_id,
        "question": example.question,
        "answer": example.answer,
        "choices": example.choices,
    }
    if dataset_name:
        d["dataset_name"] = dataset_name
    if example.example_metadata:
        d["metadata"] = example.example_metadata
    return d


def to_json(examples, dataset_names: dict[int, str] | None = None) -> str:
    """Export examples as a JSON array string."""
    dataset_names = dataset_names or {}
    data = [_example_to_dict(ex, dataset_names.get(ex.dataset_id)) for ex in examples]
    return json.dumps(data, indent=2, ensure_ascii=False)


def to_jsonl(examples, dataset_names: dict[int, str] | None = None) -> str:
    """Export examples as JSONL (one JSON object per line)."""
    dataset_names = dataset_names or {}
    lines = []
    for ex in examples:
        d = _example_to_dict(ex, dataset_names.get(ex.dataset_id))
        line = json.dumps(d, ensure_ascii=False)
        lines.append(line)
    return "\n".join(lines) + "\n" if lines else ""


def to_csv(examples, dataset_names: dict[int, str] | None = None) -> str:
    """Export examples as CSV."""
    dataset_names = dataset_names or {}
    output = io.StringIO()
    fieldnames = ["id", "dataset_id", "dataset_name", "question", "answer", "choices", "metadata"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for ex in examples:
        row = _example_to_dict(ex, dataset_names.get(ex.dataset_id))
        # Serialize complex fields to JSON strings for CSV
        if row.get("choices"):
            row["choices"] = json.dumps(row["choices"])
        if row.get("metadata"):
            row["metadata"] = json.dumps(row["metadata"])
        writer.writerow(row)

    return output.getvalue()
