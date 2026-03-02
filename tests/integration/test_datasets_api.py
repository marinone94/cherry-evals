"""Integration tests for dataset API endpoints."""


def test_list_datasets_empty(test_client):
    """Test listing datasets when none exist."""
    response = test_client.get("/datasets")

    assert response.status_code == 200
    data = response.json()
    assert data["datasets"] == []
    assert data["total"] == 0


def test_list_datasets_with_data(test_client, test_db_session):
    """Test listing datasets when datasets exist."""
    from db.postgres.models import Dataset

    dataset = Dataset(
        name="TestDataset",
        source="test",
        task_type="classification",
        description="A test dataset",
    )
    test_db_session.add(dataset)
    test_db_session.flush()

    response = test_client.get("/datasets")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["datasets"][0]["name"] == "TestDataset"
    assert data["datasets"][0]["task_type"] == "classification"


def test_get_dataset_by_id(test_client, test_db_session):
    """Test getting a single dataset by ID."""
    from db.postgres.models import Dataset

    dataset = Dataset(
        name="SingleDataset",
        source="test",
        task_type="qa",
        description="Test",
    )
    test_db_session.add(dataset)
    test_db_session.flush()

    response = test_client.get(f"/datasets/{dataset.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "SingleDataset"
    assert data["id"] == dataset.id


def test_get_dataset_not_found(test_client):
    """Test getting a non-existent dataset returns 404."""
    response = test_client.get("/datasets/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Dataset not found"


def test_get_dataset_stats(test_client, test_db_session):
    """Test getting dataset statistics."""
    from db.postgres.models import Dataset, Example

    dataset = Dataset(
        name="StatsDataset",
        source="test",
        task_type="classification",
        stats={"total": 2},
    )
    test_db_session.add(dataset)
    test_db_session.flush()

    for i in range(2):
        example = Example(
            dataset_id=dataset.id,
            question=f"Question {i}",
            answer=f"Answer {i}",
        )
        test_db_session.add(example)
    test_db_session.flush()

    response = test_client.get(f"/datasets/{dataset.id}/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["example_count"] == 2
    assert data["dataset_name"] == "StatsDataset"
