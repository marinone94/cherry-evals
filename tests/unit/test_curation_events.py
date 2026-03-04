"""Unit tests for curation event tracking service."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from core.traces.events import (
    get_co_picked_examples,
    get_event_stats,
    get_example_pick_count,
    get_popular_examples,
    record_event,
)
from db.postgres.base import Base
from db.postgres.models import Collection, CurationEvent, Dataset, Example


@pytest.fixture(scope="module")
def engine():
    """Create an in-memory SQLite engine for unit tests."""
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture
def db_session(engine):
    """Provide a transactional session that is rolled back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = session_factory()

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def end_savepoint(session, txn):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


def _seed_dataset_and_examples(session, count=3, ds_name="TestDS"):
    """Seed a dataset with examples for testing."""
    dataset = Dataset(name=ds_name, source="test", task_type="qa")
    session.add(dataset)
    session.flush()

    examples = []
    for i in range(count):
        ex = Example(
            dataset_id=dataset.id,
            question=f"Q{i}?",
            answer=f"A{i}",
        )
        session.add(ex)
        examples.append(ex)
    session.flush()
    return dataset, examples


def _seed_collection(session, name="TestColl"):
    """Seed a collection."""
    coll = Collection(name=name)
    session.add(coll)
    session.flush()
    return coll


# ---------------------------------------------------------------------------
# record_event tests
# ---------------------------------------------------------------------------


def test_record_event_creates_curation_event(db_session):
    """record_event should create a CurationEvent row and return it."""
    event_obj = record_event(
        db=db_session,
        event_type="search",
        session_id="sess-abc",
        query="transformer models",
        search_mode="keyword",
    )

    assert event_obj is not None
    assert event_obj.event_type == "search"
    assert event_obj.session_id == "sess-abc"
    assert event_obj.query == "transformer models"
    assert event_obj.search_mode == "keyword"
    assert event_obj.id is not None


def test_record_event_pick(db_session):
    """record_event should record pick events with example and collection context."""
    _, examples = _seed_dataset_and_examples(db_session, ds_name="DS_pick")
    coll = _seed_collection(db_session, name="Coll_pick")

    event_obj = record_event(
        db=db_session,
        event_type="pick",
        example_id=examples[0].id,
        collection_id=coll.id,
        dataset_id=examples[0].dataset_id,
    )

    assert event_obj is not None
    assert event_obj.event_type == "pick"
    assert event_obj.example_id == examples[0].id
    assert event_obj.collection_id == coll.id


def test_record_event_remove(db_session):
    """record_event should record remove events."""
    _, examples = _seed_dataset_and_examples(db_session, ds_name="DS_remove")
    coll = _seed_collection(db_session, name="Coll_remove")

    event_obj = record_event(
        db=db_session,
        event_type="remove",
        example_id=examples[0].id,
        collection_id=coll.id,
    )

    assert event_obj is not None
    assert event_obj.event_type == "remove"


def test_record_event_export(db_session):
    """record_event should record export events with format context."""
    coll = _seed_collection(db_session, name="Coll_export")

    event_obj = record_event(
        db=db_session,
        event_type="export",
        collection_id=coll.id,
        export_format="json",
    )

    assert event_obj is not None
    assert event_obj.event_type == "export"
    assert event_obj.export_format == "json"


def test_record_event_handles_failure_gracefully(db_session, monkeypatch):
    """record_event should return None and not raise when DB insert fails."""
    original_add = db_session.add

    def broken_add(obj):
        if isinstance(obj, CurationEvent):
            raise RuntimeError("Simulated DB failure")
        return original_add(obj)

    monkeypatch.setattr(db_session, "add", broken_add)

    # Should not raise
    result = record_event(db=db_session, event_type="search", query="test")
    assert result is None


def test_record_event_with_metadata(db_session):
    """record_event should persist event_metadata correctly."""
    event_obj = record_event(
        db=db_session,
        event_type="search",
        metadata={"extra_key": "extra_value", "count": 42},
    )

    assert event_obj is not None
    assert event_obj.event_metadata == {"extra_key": "extra_value", "count": 42}


# ---------------------------------------------------------------------------
# get_event_stats tests
# ---------------------------------------------------------------------------


def test_get_event_stats_empty(db_session):
    """get_event_stats on an empty database should return zero counts."""
    stats = get_event_stats(db=db_session)

    assert stats["total_events"] == 0
    assert stats["events_by_type"] == {}
    assert stats["most_searched_queries"] == []
    assert stats["most_picked_examples"] == []


def test_get_event_stats_with_events(db_session):
    """get_event_stats should correctly aggregate events."""
    record_event(db=db_session, event_type="search", query="cats")
    record_event(db=db_session, event_type="search", query="dogs")
    record_event(db=db_session, event_type="search", query="cats")
    record_event(db=db_session, event_type="pick")
    record_event(db=db_session, event_type="export", export_format="json")

    stats = get_event_stats(db=db_session)

    assert stats["total_events"] == 5
    assert stats["events_by_type"]["search"] == 3
    assert stats["events_by_type"]["pick"] == 1
    assert stats["events_by_type"]["export"] == 1

    # "cats" searched twice should appear first in most_searched_queries
    queries = stats["most_searched_queries"]
    assert len(queries) >= 2
    assert queries[0]["query"] == "cats"
    assert queries[0]["count"] == 2


# ---------------------------------------------------------------------------
# get_example_pick_count tests
# ---------------------------------------------------------------------------


def test_get_example_pick_count_zero(db_session):
    """An example that has never been picked should have a count of 0."""
    _, examples = _seed_dataset_and_examples(db_session, ds_name="DS_pick_count_zero")
    count = get_example_pick_count(db=db_session, example_id=examples[0].id)
    assert count == 0


def test_get_example_pick_count(db_session):
    """get_example_pick_count should count pick events for a specific example."""
    _, examples = _seed_dataset_and_examples(db_session, ds_name="DS_pick_count")

    record_event(db=db_session, event_type="pick", example_id=examples[0].id)
    record_event(db=db_session, event_type="pick", example_id=examples[0].id)
    record_event(db=db_session, event_type="pick", example_id=examples[1].id)
    # Non-pick event should not count
    record_event(db=db_session, event_type="remove", example_id=examples[0].id)

    assert get_example_pick_count(db=db_session, example_id=examples[0].id) == 2
    assert get_example_pick_count(db=db_session, example_id=examples[1].id) == 1


# ---------------------------------------------------------------------------
# get_popular_examples tests
# ---------------------------------------------------------------------------


def test_get_popular_examples_empty(db_session):
    """get_popular_examples on an empty database should return an empty list."""
    results = get_popular_examples(db=db_session, limit=10)
    assert results == []


def test_get_popular_examples_sorted(db_session):
    """get_popular_examples should return examples sorted by pick_count desc."""
    _, examples = _seed_dataset_and_examples(db_session, ds_name="DS_popular", count=3)

    # Pick example[0] three times, example[1] once, example[2] twice
    for _ in range(3):
        record_event(db=db_session, event_type="pick", example_id=examples[0].id)
    record_event(db=db_session, event_type="pick", example_id=examples[1].id)
    for _ in range(2):
        record_event(db=db_session, event_type="pick", example_id=examples[2].id)

    popular = get_popular_examples(db=db_session, limit=3)

    assert len(popular) == 3
    assert popular[0]["example_id"] == examples[0].id
    assert popular[0]["pick_count"] == 3
    assert popular[1]["example_id"] == examples[2].id
    assert popular[1]["pick_count"] == 2
    assert popular[2]["example_id"] == examples[1].id
    assert popular[2]["pick_count"] == 1


def test_get_popular_examples_limit(db_session):
    """get_popular_examples should respect the limit parameter."""
    _, examples = _seed_dataset_and_examples(db_session, ds_name="DS_popular_limit", count=5)
    for ex in examples:
        record_event(db=db_session, event_type="pick", example_id=ex.id)

    popular = get_popular_examples(db=db_session, limit=2)
    assert len(popular) == 2


# ---------------------------------------------------------------------------
# get_co_picked_examples tests
# ---------------------------------------------------------------------------


def test_get_co_picked_examples_no_events(db_session):
    """get_co_picked_examples should return empty list when no pick events exist."""
    _, examples = _seed_dataset_and_examples(db_session, ds_name="DS_co_empty")
    results = get_co_picked_examples(db=db_session, example_id=examples[0].id)
    assert results == []


def test_get_co_picked_examples(db_session):
    """get_co_picked_examples should find examples picked in the same collections."""
    _, examples = _seed_dataset_and_examples(db_session, ds_name="DS_co", count=4)
    coll1 = _seed_collection(db_session, name="Coll_co_1")
    coll2 = _seed_collection(db_session, name="Coll_co_2")

    # examples[0] and examples[1] in coll1
    record_event(
        db=db_session, event_type="pick", example_id=examples[0].id, collection_id=coll1.id
    )
    record_event(
        db=db_session, event_type="pick", example_id=examples[1].id, collection_id=coll1.id
    )
    # examples[0] and examples[2] in coll2
    record_event(
        db=db_session, event_type="pick", example_id=examples[0].id, collection_id=coll2.id
    )
    record_event(
        db=db_session, event_type="pick", example_id=examples[2].id, collection_id=coll2.id
    )
    # examples[3] picked with no shared collection with examples[0]
    coll3 = _seed_collection(db_session, name="Coll_co_3")
    record_event(
        db=db_session, event_type="pick", example_id=examples[3].id, collection_id=coll3.id
    )

    co_picked = get_co_picked_examples(db=db_session, example_id=examples[0].id)

    co_picked_ids = [r["example_id"] for r in co_picked]
    # examples[1] and examples[2] should appear; examples[3] should not
    assert examples[1].id in co_picked_ids
    assert examples[2].id in co_picked_ids
    assert examples[3].id not in co_picked_ids
    # examples[0] itself should not appear
    assert examples[0].id not in co_picked_ids


def test_get_co_picked_examples_limit(db_session):
    """get_co_picked_examples should respect the limit parameter."""
    _, examples = _seed_dataset_and_examples(db_session, ds_name="DS_co_limit", count=6)
    coll = _seed_collection(db_session, name="Coll_co_limit")

    for ex in examples:
        record_event(db=db_session, event_type="pick", example_id=ex.id, collection_id=coll.id)

    results = get_co_picked_examples(db=db_session, example_id=examples[0].id, limit=3)
    assert len(results) <= 3
