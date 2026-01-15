"""Integration tests for FastAPI endpoints."""


def test_root_endpoint(test_client):
    """Test that root endpoint returns welcome message."""
    response = test_client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Cherry Evals API"}


def test_health_endpoint(test_client):
    """Test that health endpoint returns status ok."""
    response = test_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_app_metadata(test_client):
    """Test that app has correct metadata."""
    response = test_client.get("/openapi.json")

    assert response.status_code == 200
    openapi = response.json()

    assert openapi["info"]["title"] == "Cherry Evals"
    assert openapi["info"]["description"] == "Curated evaluation dataset search and export platform"
    assert openapi["info"]["version"] == "0.1.0"


def test_nonexistent_route_returns_404(test_client):
    """Test that non-existent routes return 404."""
    response = test_client.get("/nonexistent")

    assert response.status_code == 404


def test_health_endpoint_method_not_allowed(test_client):
    """Test that health endpoint only accepts GET."""
    response = test_client.post("/health")

    assert response.status_code == 405


def test_openapi_schema_available(test_client):
    """Test that OpenAPI schema is available."""
    response = test_client.get("/openapi.json")

    assert response.status_code == 200
    assert "openapi" in response.json()
    assert "info" in response.json()
    assert "paths" in response.json()


def test_docs_available(test_client):
    """Test that API docs are available."""
    response = test_client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
