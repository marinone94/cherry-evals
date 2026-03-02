"""Integration tests for collection API endpoints."""

from db.postgres.models import Dataset, Example


def _seed_examples(db_session, count=3):
    """Helper to seed dataset and examples for collection tests."""
    dataset = Dataset(name="CollDS", source="test", task_type="qa")
    db_session.add(dataset)
    db_session.flush()

    examples = []
    for i in range(count):
        ex = Example(
            dataset_id=dataset.id,
            question=f"Question {i}?",
            answer=f"Answer {i}",
        )
        db_session.add(ex)
        examples.append(ex)
    db_session.flush()
    return dataset, examples


def test_create_collection(test_client):
    """Test creating a new collection."""
    response = test_client.post(
        "/collections", json={"name": "My Eval Set", "description": "Test collection"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Eval Set"
    assert data["description"] == "Test collection"
    assert data["example_count"] == 0
    assert "id" in data


def test_list_collections_empty(test_client):
    """Test listing collections when none exist."""
    response = test_client.get("/collections")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


def test_list_collections(test_client, test_db_session):
    """Test listing collections."""
    from db.postgres.models import Collection

    test_db_session.add(Collection(name="Collection A"))
    test_db_session.add(Collection(name="Collection B"))
    test_db_session.flush()

    response = test_client.get("/collections")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_get_collection_by_id(test_client, test_db_session):
    """Test getting a collection by ID."""
    from db.postgres.models import Collection

    coll = Collection(name="Get Me", description="Found it")
    test_db_session.add(coll)
    test_db_session.flush()

    response = test_client.get(f"/collections/{coll.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Get Me"
    assert data["description"] == "Found it"


def test_get_collection_not_found(test_client):
    """Test getting a non-existent collection."""
    response = test_client.get("/collections/99999")
    assert response.status_code == 404


def test_update_collection(test_client, test_db_session):
    """Test updating a collection."""
    from db.postgres.models import Collection

    coll = Collection(name="Old Name")
    test_db_session.add(coll)
    test_db_session.flush()

    response = test_client.put(
        f"/collections/{coll.id}",
        json={"name": "New Name", "description": "Updated"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "Updated"


def test_delete_collection(test_client, test_db_session):
    """Test deleting a collection."""
    from db.postgres.models import Collection

    coll = Collection(name="Delete Me")
    test_db_session.add(coll)
    test_db_session.flush()
    coll_id = coll.id

    response = test_client.delete(f"/collections/{coll_id}")
    assert response.status_code == 204

    response = test_client.get(f"/collections/{coll_id}")
    assert response.status_code == 404


def test_add_examples_to_collection(test_client, test_db_session):
    """Test adding examples to a collection."""
    _, examples = _seed_examples(test_db_session)
    from db.postgres.models import Collection

    coll = Collection(name="Add Test")
    test_db_session.add(coll)
    test_db_session.flush()

    example_ids = [ex.id for ex in examples]
    response = test_client.post(
        f"/collections/{coll.id}/examples",
        json={"example_ids": example_ids},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["added"] == 3
    assert data["skipped"] == 0


def test_add_examples_skips_duplicates(test_client, test_db_session):
    """Test that adding duplicate examples is handled gracefully."""
    _, examples = _seed_examples(test_db_session, count=2)
    from db.postgres.models import Collection

    coll = Collection(name="Dup Test")
    test_db_session.add(coll)
    test_db_session.flush()

    example_ids = [examples[0].id]

    # Add once
    test_client.post(f"/collections/{coll.id}/examples", json={"example_ids": example_ids})

    # Add again — should skip
    response = test_client.post(
        f"/collections/{coll.id}/examples", json={"example_ids": example_ids}
    )
    data = response.json()
    assert data["added"] == 0
    assert data["skipped"] == 1


def test_list_collection_examples(test_client, test_db_session):
    """Test listing examples in a collection."""
    _, examples = _seed_examples(test_db_session)
    from db.postgres.models import Collection

    coll = Collection(name="List Test")
    test_db_session.add(coll)
    test_db_session.flush()

    example_ids = [ex.id for ex in examples]
    test_client.post(f"/collections/{coll.id}/examples", json={"example_ids": example_ids})

    response = test_client.get(f"/collections/{coll.id}/examples")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["collection_id"] == coll.id
    assert len(data["examples"]) == 3


def test_remove_example_from_collection(test_client, test_db_session):
    """Test removing a single example from a collection."""
    _, examples = _seed_examples(test_db_session)
    from db.postgres.models import Collection

    coll = Collection(name="Remove Test")
    test_db_session.add(coll)
    test_db_session.flush()

    example_ids = [ex.id for ex in examples]
    test_client.post(f"/collections/{coll.id}/examples", json={"example_ids": example_ids})

    # Remove one
    response = test_client.delete(f"/collections/{coll.id}/examples/{examples[0].id}")
    assert response.status_code == 204

    # Verify it's gone
    response = test_client.get(f"/collections/{coll.id}/examples")
    data = response.json()
    assert data["total"] == 2


def test_bulk_remove_examples(test_client, test_db_session):
    """Test bulk removing examples from a collection."""
    _, examples = _seed_examples(test_db_session)
    from db.postgres.models import Collection

    coll = Collection(name="Bulk Remove")
    test_db_session.add(coll)
    test_db_session.flush()

    example_ids = [ex.id for ex in examples]
    test_client.post(f"/collections/{coll.id}/examples", json={"example_ids": example_ids})

    # Bulk remove first two
    response = test_client.post(
        f"/collections/{coll.id}/examples/bulk-remove",
        json={"example_ids": [examples[0].id, examples[1].id]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["removed"] == 2

    # Verify
    response = test_client.get(f"/collections/{coll.id}/examples")
    assert response.json()["total"] == 1


def test_collection_example_count_updates(test_client, test_db_session):
    """Test that example_count in collection response reflects actual count."""
    _, examples = _seed_examples(test_db_session)
    from db.postgres.models import Collection

    coll = Collection(name="Count Test")
    test_db_session.add(coll)
    test_db_session.flush()

    # Initially 0
    response = test_client.get(f"/collections/{coll.id}")
    assert response.json()["example_count"] == 0

    # Add examples
    test_client.post(
        f"/collections/{coll.id}/examples",
        json={"example_ids": [examples[0].id, examples[1].id]},
    )

    response = test_client.get(f"/collections/{coll.id}")
    assert response.json()["example_count"] == 2
