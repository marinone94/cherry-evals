"""Unit tests for MCP server tools.

Tests the MCP tool functions directly (they're regular functions
that return JSON strings) using the test database.
"""

import json

import pytest

from db.postgres.models import Collection, CollectionExample, Dataset, Example


@pytest.fixture
def seeded_db(test_db_session):
    """Seed the test database with datasets and examples."""
    ds = Dataset(name="TestDS", source="test", task_type="qa", description="Test dataset")
    test_db_session.add(ds)
    test_db_session.flush()

    examples = []
    for i in range(5):
        ex = Example(
            dataset_id=ds.id,
            question=f"What is {i}+{i}?",
            answer=str(i + i),
            choices=[str(i), str(i + i), str(i * 3)],
            example_metadata={"subject": "math", "index": i},
        )
        test_db_session.add(ex)
        examples.append(ex)
    test_db_session.flush()

    return ds, examples


@pytest.fixture
def _patch_session(test_db_session, monkeypatch):
    """Patch _get_db in the MCP server to use the test session."""
    monkeypatch.setattr("mcp_server.server._get_db", lambda: test_db_session)


@pytest.mark.usefixtures("_patch_session")
class TestListDatasets:
    def test_empty(self):
        from mcp_server.server import list_datasets

        result = json.loads(list_datasets())
        assert result == []

    def test_with_data(self, seeded_db):
        from mcp_server.server import list_datasets

        result = json.loads(list_datasets())
        assert len(result) == 1
        assert result[0]["name"] == "TestDS"
        assert result[0]["example_count"] == 5


@pytest.mark.usefixtures("_patch_session")
class TestGetDataset:
    def test_found(self, seeded_db):
        from mcp_server.server import get_dataset

        ds, _ = seeded_db
        result = json.loads(get_dataset(ds.id))
        assert result["name"] == "TestDS"
        assert result["example_count"] == 5

    def test_not_found(self):
        from mcp_server.server import get_dataset

        result = json.loads(get_dataset(99999))
        assert "error" in result


@pytest.mark.usefixtures("_patch_session")
class TestSearchExamples:
    def test_basic_search(self, seeded_db):
        from mcp_server.server import search_examples

        result = json.loads(search_examples("What is"))
        assert result["total"] == 5
        assert len(result["results"]) == 5

    def test_search_specific(self, seeded_db):
        from mcp_server.server import search_examples

        result = json.loads(search_examples("3+3"))
        assert result["total"] == 1
        assert result["results"][0]["answer"] == "6"

    def test_search_with_limit(self, seeded_db):
        from mcp_server.server import search_examples

        result = json.loads(search_examples("What is", limit=2))
        assert len(result["results"]) == 2
        assert result["total"] == 5

    def test_limit_capped_at_100(self, seeded_db):
        from mcp_server.server import search_examples

        # Should not error even with limit > 100
        result = json.loads(search_examples("What is", limit=200))
        assert len(result["results"]) == 5


@pytest.mark.usefixtures("_patch_session")
class TestCollectionTools:
    def test_create_collection(self):
        from mcp_server.server import create_collection

        result = json.loads(create_collection("Test Collection", "A test"))
        assert result["name"] == "Test Collection"
        assert result["description"] == "A test"
        assert "id" in result

    def test_list_collections(self, test_db_session):
        from mcp_server.server import list_collections

        test_db_session.add(Collection(name="Coll A"))
        test_db_session.add(Collection(name="Coll B"))
        test_db_session.flush()

        result = json.loads(list_collections())
        assert len(result) == 2

    def test_add_to_collection(self, seeded_db, test_db_session):
        from mcp_server.server import add_to_collection

        ds, examples = seeded_db
        coll = Collection(name="Add Test")
        test_db_session.add(coll)
        test_db_session.flush()

        ids = [examples[0].id, examples[1].id]
        result = json.loads(add_to_collection(coll.id, ids))
        assert result["added"] == 2
        assert result["skipped_duplicates"] == 0

    def test_add_skips_duplicates(self, seeded_db, test_db_session):
        from mcp_server.server import add_to_collection

        ds, examples = seeded_db
        coll = Collection(name="Dup Test")
        test_db_session.add(coll)
        test_db_session.flush()

        test_db_session.add(CollectionExample(collection_id=coll.id, example_id=examples[0].id))
        test_db_session.flush()

        result = json.loads(add_to_collection(coll.id, [examples[0].id, examples[1].id]))
        assert result["added"] == 1
        assert result["skipped_duplicates"] == 1

    def test_add_to_nonexistent_collection(self):
        from mcp_server.server import add_to_collection

        result = json.loads(add_to_collection(99999, [1]))
        assert "error" in result

    def test_get_collection(self, seeded_db, test_db_session):
        from mcp_server.server import get_collection

        ds, examples = seeded_db
        coll = Collection(name="Get Test")
        test_db_session.add(coll)
        test_db_session.flush()

        test_db_session.add(CollectionExample(collection_id=coll.id, example_id=examples[0].id))
        test_db_session.flush()

        result = json.loads(get_collection(coll.id))
        assert result["name"] == "Get Test"
        assert result["example_count"] == 1
        assert len(result["examples"]) == 1

    def test_get_collection_not_found(self):
        from mcp_server.server import get_collection

        result = json.loads(get_collection(99999))
        assert "error" in result


@pytest.mark.usefixtures("_patch_session")
class TestExportCollection:
    def test_export_json(self, seeded_db, test_db_session):
        from mcp_server.server import export_collection

        ds, examples = seeded_db
        coll = Collection(name="Export JSON")
        test_db_session.add(coll)
        test_db_session.flush()
        for ex in examples[:2]:
            test_db_session.add(CollectionExample(collection_id=coll.id, example_id=ex.id))
        test_db_session.flush()

        result = export_collection(coll.id, format="json")
        data = json.loads(result)
        assert len(data) == 2

    def test_export_jsonl(self, seeded_db, test_db_session):
        from mcp_server.server import export_collection

        ds, examples = seeded_db
        coll = Collection(name="Export JSONL")
        test_db_session.add(coll)
        test_db_session.flush()
        test_db_session.add(CollectionExample(collection_id=coll.id, example_id=examples[0].id))
        test_db_session.flush()

        result = export_collection(coll.id, format="jsonl")
        lines = result.strip().split("\n")
        assert len(lines) == 1
        assert json.loads(lines[0])["dataset_name"] == "TestDS"

    def test_export_csv(self, seeded_db, test_db_session):
        from mcp_server.server import export_collection

        ds, examples = seeded_db
        coll = Collection(name="Export CSV")
        test_db_session.add(coll)
        test_db_session.flush()
        test_db_session.add(CollectionExample(collection_id=coll.id, example_id=examples[0].id))
        test_db_session.flush()

        result = export_collection(coll.id, format="csv")
        assert "question" in result
        assert "What is 0+0?" in result

    def test_export_invalid_format(self, seeded_db, test_db_session):
        from mcp_server.server import export_collection

        ds, _ = seeded_db
        coll = Collection(name="Bad Format")
        test_db_session.add(coll)
        test_db_session.flush()

        result = json.loads(export_collection(coll.id, format="xml"))
        assert "error" in result

    def test_export_not_found(self):
        from mcp_server.server import export_collection

        result = json.loads(export_collection(99999))
        assert "error" in result
