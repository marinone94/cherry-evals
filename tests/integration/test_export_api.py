"""Integration tests for export API endpoints."""

import csv
import io
import json

from db.postgres.models import Collection, CollectionExample, Dataset, Example


def _seed_collection_with_examples(db_session, name="Export Test", count=3):
    """Seed a collection with examples for export testing."""
    dataset = Dataset(name=f"DS-{name}", source="test", task_type="qa")
    db_session.add(dataset)
    db_session.flush()

    coll = Collection(name=name, description="Test export collection")
    db_session.add(coll)
    db_session.flush()

    examples = []
    for i in range(count):
        ex = Example(
            dataset_id=dataset.id,
            question=f"Question {i}?",
            answer=f"Answer {i}",
            choices=[f"A{i}", f"B{i}", f"C{i}"] if i % 2 == 0 else None,
            example_metadata={"subject": "math", "index": i} if i == 0 else None,
        )
        db_session.add(ex)
        examples.append(ex)
    db_session.flush()

    for ex in examples:
        db_session.add(CollectionExample(collection_id=coll.id, example_id=ex.id))
    db_session.flush()

    return coll, dataset, examples


class TestExportJson:
    def test_export_json(self, test_client, test_db_session):
        coll, dataset, examples = _seed_collection_with_examples(test_db_session)

        response = test_client.post(
            f"/collections/{coll.id}/export",
            json={"format": "json"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "attachment" in response.headers["content-disposition"]

        data = response.json()
        assert len(data) == 3
        assert data[0]["question"] == "Question 0?"
        assert data[0]["dataset_name"] == dataset.name

    def test_export_json_empty_collection(self, test_client, test_db_session):
        coll = Collection(name="Empty")
        test_db_session.add(coll)
        test_db_session.flush()

        response = test_client.post(
            f"/collections/{coll.id}/export",
            json={"format": "json"},
        )

        assert response.status_code == 200
        assert response.json() == []


class TestExportJsonl:
    def test_export_jsonl(self, test_client, test_db_session):
        coll, dataset, examples = _seed_collection_with_examples(test_db_session)

        response = test_client.post(
            f"/collections/{coll.id}/export",
            json={"format": "jsonl"},
        )

        assert response.status_code == 200
        assert "ndjson" in response.headers["content-type"]

        lines = response.text.strip().split("\n")
        assert len(lines) == 3
        first = json.loads(lines[0])
        assert first["question"] == "Question 0?"
        assert first["dataset_name"] == dataset.name

    def test_export_jsonl_preserves_metadata(self, test_client, test_db_session):
        coll, _, _ = _seed_collection_with_examples(test_db_session)

        response = test_client.post(
            f"/collections/{coll.id}/export",
            json={"format": "jsonl"},
        )

        lines = response.text.strip().split("\n")
        first = json.loads(lines[0])
        assert first["metadata"] == {"subject": "math", "index": 0}


class TestExportCsv:
    def test_export_csv(self, test_client, test_db_session):
        coll, dataset, _ = _seed_collection_with_examples(test_db_session)

        response = test_client.post(
            f"/collections/{coll.id}/export",
            json={"format": "csv"},
        )

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

        reader = csv.DictReader(io.StringIO(response.text))
        rows = list(reader)
        assert len(rows) == 3
        assert rows[0]["question"] == "Question 0?"
        assert rows[0]["dataset_name"] == dataset.name

    def test_csv_choices_serialized(self, test_client, test_db_session):
        coll, _, _ = _seed_collection_with_examples(test_db_session)

        response = test_client.post(
            f"/collections/{coll.id}/export",
            json={"format": "csv"},
        )

        reader = csv.DictReader(io.StringIO(response.text))
        rows = list(reader)
        # First example has choices
        assert json.loads(rows[0]["choices"]) == ["A0", "B0", "C0"]


class TestExportNotFound:
    def test_export_nonexistent_collection(self, test_client):
        response = test_client.post(
            "/collections/99999/export",
            json={"format": "json"},
        )
        assert response.status_code == 404

    def test_export_invalid_format(self, test_client, test_db_session):
        coll = Collection(name="Invalid Format")
        test_db_session.add(coll)
        test_db_session.flush()

        response = test_client.post(
            f"/collections/{coll.id}/export",
            json={"format": "xml"},
        )
        assert response.status_code == 422


class TestExportFilename:
    def test_filename_in_disposition(self, test_client, test_db_session):
        coll = Collection(name="My Test Collection")
        test_db_session.add(coll)
        test_db_session.flush()

        response = test_client.post(
            f"/collections/{coll.id}/export",
            json={"format": "json"},
        )

        disposition = response.headers["content-disposition"]
        assert "my_test_collection.json" in disposition

    def test_jsonl_extension(self, test_client, test_db_session):
        coll = Collection(name="JSONL Test")
        test_db_session.add(coll)
        test_db_session.flush()

        response = test_client.post(
            f"/collections/{coll.id}/export",
            json={"format": "jsonl"},
        )

        assert "jsonl_test.jsonl" in response.headers["content-disposition"]

    def test_csv_extension(self, test_client, test_db_session):
        coll = Collection(name="CSV Test")
        test_db_session.add(coll)
        test_db_session.flush()

        response = test_client.post(
            f"/collections/{coll.id}/export",
            json={"format": "csv"},
        )

        assert "csv_test.csv" in response.headers["content-disposition"]


class TestExportLangfuseValidation:
    def test_langfuse_without_credentials_returns_502(
        self, test_client, test_db_session, monkeypatch
    ):
        """When Langfuse credentials are not set, returns 502."""
        coll, _, _ = _seed_collection_with_examples(test_db_session, name="LF Test")

        # Ensure Langfuse creds are empty
        monkeypatch.setattr("core.export.langfuse_export.settings.langfuse_public_key", "")
        monkeypatch.setattr("core.export.langfuse_export.settings.langfuse_secret_key", "")

        response = test_client.post(
            f"/collections/{coll.id}/export",
            json={"format": "langfuse"},
        )

        assert response.status_code == 502
        assert "credentials" in response.json()["detail"].lower()
