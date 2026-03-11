"""Integration tests for search filters, sort options, and facets endpoint."""


# ── Seed helper ──────────────────────────────────────────────────────────────


def _seed(db):
    """Insert two datasets with typed examples for filter/sort testing."""
    from db.postgres.models import Dataset, Example

    ds_mc = Dataset(name="FilterMC", source="test", task_type="multiple_choice")
    ds_oe = Dataset(name="FilterOE", source="test", task_type="open_ended")
    db.add_all([ds_mc, ds_oe])
    db.flush()

    examples = [
        Example(
            dataset_id=ds_mc.id,
            question="What is the capital of France?",
            answer="Paris",
            example_metadata={"subject": "geography"},
        ),
        Example(
            dataset_id=ds_mc.id,
            question="What is photosynthesis?",
            answer="Process by which plants use sunlight",
            example_metadata={"subject": "biology"},
        ),
        Example(
            dataset_id=ds_oe.id,
            question="Calculate 2 + 2",
            answer="4",
            example_metadata={"subject": "math"},
        ),
        Example(
            dataset_id=ds_oe.id,
            question="What is the capital of Germany?",
            answer="Berlin",
            example_metadata={"subject": "geography"},
        ),
    ]
    db.add_all(examples)
    db.flush()
    return ds_mc, ds_oe


# ── task_type filter ──────────────────────────────────────────────────────────


def test_search_task_type_filter(test_client, test_db_session):
    """Keyword search with task_type filter returns only matching task type."""
    _seed(test_db_session)

    resp = test_client.post(
        "/search",
        json={"query": "capital", "task_type": "multiple_choice"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    # All returned results must come from a multiple_choice dataset
    for r in data["results"]:
        assert r["dataset_name"] == "FilterMC"


def test_search_task_type_filter_open_ended(test_client, test_db_session):
    """Keyword search with open_ended task_type filter excludes multiple_choice."""
    _seed(test_db_session)

    resp = test_client.post(
        "/search",
        json={"query": "capital", "task_type": "open_ended"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # "capital of Germany" is in open_ended dataset only
    assert data["total"] >= 1
    for r in data["results"]:
        assert r["dataset_name"] == "FilterOE"


def test_search_task_type_no_match(test_client, test_db_session):
    """Keyword search with non-existent task_type returns empty results."""
    _seed(test_db_session)

    resp = test_client.post(
        "/search",
        json={"query": "capital", "task_type": "nonexistent_type"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["results"] == []


# ── sort_by ───────────────────────────────────────────────────────────────────


def test_search_sort_relevance_default(test_client, test_db_session):
    """Default sort_by=relevance returns results ordered by id ascending."""
    _seed(test_db_session)

    resp = test_client.post("/search", json={"query": "What"})
    assert resp.status_code == 200
    data = resp.json()
    ids = [r["id"] for r in data["results"]]
    assert ids == sorted(ids), "relevance sort should produce ascending id order"


def test_search_sort_newest(test_client, test_db_session):
    """sort_by=newest is accepted and returns results (order depends on timestamps)."""
    _seed(test_db_session)

    resp = test_client.post("/search", json={"query": "What", "sort_by": "newest"})
    assert resp.status_code == 200
    data = resp.json()
    # The request must succeed and return results; exact order depends on
    # created_at precision which may be identical in SQLite test fixtures.
    assert data["total"] >= 1
    assert len(data["results"]) >= 1


def test_search_sort_dataset(test_client, test_db_session):
    """sort_by=dataset returns results ordered by dataset name then question."""
    _seed(test_db_session)

    resp = test_client.post("/search", json={"query": "What", "sort_by": "dataset"})
    assert resp.status_code == 200
    data = resp.json()
    names = [r["dataset_name"] for r in data["results"]]
    # Should be grouped by dataset name (sorted)
    assert names == sorted(names), "dataset sort should group by dataset name"


def test_search_sort_invalid_rejected(test_client, test_db_session):
    """Unknown sort_by value is rejected with 422 (validated via Literal type)."""
    _seed(test_db_session)

    resp = test_client.post("/search", json={"query": "capital", "sort_by": "unknown_sort"})
    assert resp.status_code == 422


# ── Facets endpoint ───────────────────────────────────────────────────────────


def test_facets_no_query(test_client, test_db_session):
    """GET /search/facets with no query returns counts for all examples."""
    _seed(test_db_session)

    resp = test_client.post("/search/facets", json={})
    assert resp.status_code == 200
    data = resp.json()

    assert "datasets" in data
    assert "subjects" in data
    assert "task_types" in data
    assert "total" in data
    assert data["total"] >= 4  # at least the 4 seeded examples


def test_facets_with_query(test_client, test_db_session):
    """GET /search/facets with query filters counts to matching examples."""
    _seed(test_db_session)

    resp = test_client.post("/search/facets", json={"query": "capital"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    # Must not return more than total examples seeded
    assert data["total"] <= 4


def test_facets_structure(test_client, test_db_session):
    """Facets response has the correct shape."""
    _seed(test_db_session)

    resp = test_client.post("/search/facets", json={})
    assert resp.status_code == 200
    data = resp.json()

    for ds in data["datasets"]:
        assert "name" in ds
        assert "count" in ds

    for subj in data["subjects"]:
        assert "name" in subj
        assert "dataset" in subj
        assert "count" in subj

    for tt in data["task_types"]:
        assert "name" in tt
        assert "count" in tt


def test_facets_dataset_counts_match_search(test_client, test_db_session):
    """Facet dataset count for 'capital' matches actual search total."""
    _seed(test_db_session)

    facet_resp = test_client.post("/search/facets", json={"query": "capital"})
    search_resp = test_client.post("/search", json={"query": "capital"})

    assert facet_resp.status_code == 200
    assert search_resp.status_code == 200

    facet_total = facet_resp.json()["total"]
    search_total = search_resp.json()["total"]
    assert facet_total == search_total


def test_facets_no_results_query(test_client, test_db_session):
    """Facets endpoint with a non-matching query returns empty lists and zero total."""
    _seed(test_db_session)

    resp = test_client.post("/search/facets", json={"query": "zzznomatch"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["datasets"] == []
    assert data["task_types"] == []


# ── Dataset subjects endpoint ─────────────────────────────────────────────────


def test_dataset_subjects_endpoint(test_client, test_db_session):
    """GET /datasets/{id}/subjects returns subject breakdown."""
    ds_mc, _ = _seed(test_db_session)

    resp = test_client.get(f"/datasets/{ds_mc.id}/subjects")
    assert resp.status_code == 200
    data = resp.json()

    assert data["dataset_id"] == ds_mc.id
    assert data["dataset_name"] == "FilterMC"
    assert "subjects" in data

    subj_names = {s["subject"] for s in data["subjects"]}
    assert "geography" in subj_names
    assert "biology" in subj_names


def test_dataset_subjects_not_found(test_client, test_db_session):
    """GET /datasets/9999/subjects returns 404 for unknown dataset."""
    resp = test_client.get("/datasets/9999/subjects")
    assert resp.status_code == 404
