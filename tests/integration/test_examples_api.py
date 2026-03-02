"""Integration tests for example API endpoints."""


def test_list_examples_empty(test_client):
    """Test listing examples when none exist."""
    response = test_client.get("/examples")

    assert response.status_code == 200
    data = response.json()
    assert data["examples"] == []
    assert data["total"] == 0
    assert data["offset"] == 0
    assert data["limit"] == 20


def test_list_examples_with_data(test_client, test_db_session):
    """Test listing examples with data."""
    from db.postgres.models import Dataset, Example

    dataset = Dataset(name="ExDataset", source="test", task_type="qa")
    test_db_session.add(dataset)
    test_db_session.flush()

    for i in range(3):
        example = Example(
            dataset_id=dataset.id,
            question=f"Question {i}?",
            answer=f"Answer {i}",
            choices=["A", "B", "C", "D"],
            example_metadata={"subject": "math"},
        )
        test_db_session.add(example)
    test_db_session.flush()

    response = test_client.get("/examples")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["examples"]) == 3


def test_list_examples_pagination(test_client, test_db_session):
    """Test examples pagination."""
    from db.postgres.models import Dataset, Example

    dataset = Dataset(name="PagDataset", source="test", task_type="qa")
    test_db_session.add(dataset)
    test_db_session.flush()

    for i in range(5):
        test_db_session.add(Example(dataset_id=dataset.id, question=f"Q{i}?", answer=f"A{i}"))
    test_db_session.flush()

    response = test_client.get("/examples?limit=2&offset=0")
    data = response.json()
    assert len(data["examples"]) == 2
    assert data["total"] == 5
    assert data["offset"] == 0
    assert data["limit"] == 2

    response = test_client.get("/examples?limit=2&offset=2")
    data = response.json()
    assert len(data["examples"]) == 2
    assert data["offset"] == 2


def test_list_examples_filter_by_dataset(test_client, test_db_session):
    """Test filtering examples by dataset_id."""
    from db.postgres.models import Dataset, Example

    ds1 = Dataset(name="FilterDS1", source="test", task_type="qa")
    ds2 = Dataset(name="FilterDS2", source="test", task_type="qa")
    test_db_session.add_all([ds1, ds2])
    test_db_session.flush()

    test_db_session.add(Example(dataset_id=ds1.id, question="Q1?", answer="A1"))
    test_db_session.add(Example(dataset_id=ds2.id, question="Q2?", answer="A2"))
    test_db_session.flush()

    response = test_client.get(f"/examples?dataset_id={ds1.id}")
    data = response.json()
    assert data["total"] == 1
    assert data["examples"][0]["dataset_id"] == ds1.id


def test_get_example_by_id(test_client, test_db_session):
    """Test getting a single example by ID."""
    from db.postgres.models import Dataset, Example

    dataset = Dataset(name="GetExDS", source="test", task_type="qa")
    test_db_session.add(dataset)
    test_db_session.flush()

    example = Example(
        dataset_id=dataset.id,
        question="What is 2+2?",
        answer="4",
        choices=["3", "4", "5", "6"],
    )
    test_db_session.add(example)
    test_db_session.flush()

    response = test_client.get(f"/examples/{example.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What is 2+2?"
    assert data["answer"] == "4"
    assert data["choices"] == ["3", "4", "5", "6"]


def test_get_example_not_found(test_client):
    """Test getting non-existent example returns 404."""
    response = test_client.get("/examples/99999")

    assert response.status_code == 404
