"""Unit tests for faceted search logic."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from db.postgres.base import Base
from db.postgres.models import Dataset, Example

# ── In-memory SQLite fixture ─────────────────────────────────────────────────


@pytest.fixture()
def db():
    """Provide a fresh in-memory SQLite session for each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _fk_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _seed(db):
    """Insert two datasets with a few examples each."""
    ds1 = Dataset(name="MMLU", source="hf", task_type="multiple_choice")
    ds2 = Dataset(name="GSM8K", source="hf", task_type="open_ended")
    db.add_all([ds1, ds2])
    db.flush()

    examples = [
        Example(
            dataset_id=ds1.id,
            question="What is anatomy?",
            answer="A",
            example_metadata={"subject": "anatomy"},
        ),
        Example(
            dataset_id=ds1.id,
            question="What is biology?",
            answer="B",
            example_metadata={"subject": "biology"},
        ),
        Example(
            dataset_id=ds1.id,
            question="What is anatomy again?",
            answer="C",
            example_metadata={"subject": "anatomy"},
        ),
        Example(
            dataset_id=ds2.id,
            question="Solve this math problem",
            answer="42",
            example_metadata={"subject": "math"},
        ),
        Example(
            dataset_id=ds2.id,
            question="Another math problem",
            answer="7",
            example_metadata={"subject": "math"},
        ),
    ]
    db.add_all(examples)
    db.flush()
    return ds1, ds2


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_facets_no_query_total(db):
    """get_facets with no query returns total == number of examples."""
    from core.search.facets import get_facets

    _seed(db)
    result = get_facets(db, query=None)
    assert result["total"] == 5


def test_facets_no_query_datasets(db):
    """get_facets with no query returns correct per-dataset counts."""
    from core.search.facets import get_facets

    _seed(db)
    result = get_facets(db, query=None)
    ds_map = {d["name"]: d["count"] for d in result["datasets"]}
    assert ds_map["MMLU"] == 3
    assert ds_map["GSM8K"] == 2


def test_facets_no_query_subjects(db):
    """get_facets with no query returns correct per-subject counts."""
    from core.search.facets import get_facets

    _seed(db)
    result = get_facets(db, query=None)
    subj_map = {s["name"]: s["count"] for s in result["subjects"]}
    assert subj_map["anatomy"] == 2
    assert subj_map["biology"] == 1
    assert subj_map["math"] == 2


def test_facets_no_query_task_types(db):
    """get_facets with no query returns correct per-task_type counts."""
    from core.search.facets import get_facets

    _seed(db)
    result = get_facets(db, query=None)
    tt_map = {t["name"]: t["count"] for t in result["task_types"]}
    assert tt_map["multiple_choice"] == 3
    assert tt_map["open_ended"] == 2


def test_facets_with_query_filters(db):
    """get_facets with a query restricts counts to matching examples."""
    from core.search.facets import get_facets

    _seed(db)
    result = get_facets(db, query="anatomy")
    # Only the two anatomy examples match
    assert result["total"] == 2
    ds_map = {d["name"]: d["count"] for d in result["datasets"]}
    assert ds_map.get("MMLU") == 2
    assert "GSM8K" not in ds_map


def test_facets_with_query_no_match(db):
    """get_facets returns zeros when query matches nothing."""
    from core.search.facets import get_facets

    _seed(db)
    result = get_facets(db, query="zzznomatch")
    assert result["total"] == 0
    assert result["datasets"] == []
    assert result["subjects"] == []
    assert result["task_types"] == []


def test_facets_empty_db(db):
    """get_facets on an empty database returns all-zero structures."""
    from core.search.facets import get_facets

    result = get_facets(db, query=None)
    assert result["total"] == 0
    assert result["datasets"] == []
    assert result["subjects"] == []
    assert result["task_types"] == []


def test_facets_subject_dataset_association(db):
    """Each subject facet entry includes the dataset it belongs to."""
    from core.search.facets import get_facets

    _seed(db)
    result = get_facets(db, query=None)
    anatomy_entries = [s for s in result["subjects"] if s["name"] == "anatomy"]
    assert len(anatomy_entries) == 1
    assert anatomy_entries[0]["dataset"] == "MMLU"
