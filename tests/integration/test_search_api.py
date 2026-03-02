"""Integration tests for search API endpoints."""


def _seed_search_data(db_session):
    """Helper to seed test data for search tests."""
    from db.postgres.models import Dataset, Example

    dataset = Dataset(name="SearchDS", source="test", task_type="classification")
    db_session.add(dataset)
    db_session.flush()

    examples = [
        Example(
            dataset_id=dataset.id,
            question="What is the capital of France?",
            answer="Paris",
            choices=["London", "Paris", "Berlin", "Madrid"],
            example_metadata={"subject": "geography"},
        ),
        Example(
            dataset_id=dataset.id,
            question="What is photosynthesis?",
            answer="Process by which plants convert sunlight to energy",
            choices=["A", "B", "C", "D"],
            example_metadata={"subject": "biology"},
        ),
        Example(
            dataset_id=dataset.id,
            question="Calculate the integral of x^2",
            answer="x^3/3 + C",
            choices=["x^2/2", "x^3/3 + C", "2x", "x^3"],
            example_metadata={"subject": "math"},
        ),
    ]
    db_session.add_all(examples)
    db_session.flush()
    return dataset


def test_search_basic(test_client, test_db_session):
    """Test basic keyword search."""
    _seed_search_data(test_db_session)

    response = test_client.post("/search", json={"query": "capital"})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["query"] == "capital"
    assert any("capital" in r["question"].lower() for r in data["results"])


def test_search_no_results(test_client, test_db_session):
    """Test search with no matching results."""
    _seed_search_data(test_db_session)

    response = test_client.post("/search", json={"query": "quantum entanglement"})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["results"] == []


def test_search_pagination(test_client, test_db_session):
    """Test search result pagination."""
    _seed_search_data(test_db_session)

    response = test_client.post("/search", json={"query": "What", "limit": 1, "offset": 0})

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 1
    assert data["limit"] == 1
    assert data["offset"] == 0


def test_search_matches_answer(test_client, test_db_session):
    """Test that search matches answer text too."""
    _seed_search_data(test_db_session)

    response = test_client.post("/search", json={"query": "Paris"})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_search_case_insensitive(test_client, test_db_session):
    """Test that search is case-insensitive."""
    _seed_search_data(test_db_session)

    response = test_client.post("/search", json={"query": "CAPITAL"})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_search_includes_dataset_name(test_client, test_db_session):
    """Test that search results include dataset_name."""
    _seed_search_data(test_db_session)

    response = test_client.post("/search", json={"query": "capital"})

    assert response.status_code == 200
    data = response.json()
    for result in data["results"]:
        assert "dataset_name" in result
        assert result["dataset_name"] == "SearchDS"


def test_search_empty_query_rejected(test_client):
    """Test that empty query is rejected."""
    response = test_client.post("/search", json={"query": ""})

    assert response.status_code == 422  # Validation error


def test_search_response_structure(test_client, test_db_session):
    """Test the full structure of search response."""
    _seed_search_data(test_db_session)

    response = test_client.post("/search", json={"query": "integral", "limit": 10, "offset": 0})

    assert response.status_code == 200
    data = response.json()

    # Check top-level fields
    assert "results" in data
    assert "total" in data
    assert "query" in data
    assert "offset" in data
    assert "limit" in data

    # Check result item structure
    if data["results"]:
        result = data["results"][0]
        assert "id" in result
        assert "dataset_id" in result
        assert "dataset_name" in result
        assert "question" in result
        assert "answer" in result
        assert "choices" in result
