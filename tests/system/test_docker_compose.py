"""System tests for Docker Compose infrastructure."""

import subprocess

import pytest
import requests
from sqlalchemy import text


@pytest.mark.slow
def test_postgres_container_healthy(docker_compose_up):
    """Test that PostgreSQL container is healthy."""
    result = subprocess.run(
        ["docker", "inspect", "--format={{.State.Health.Status}}", "cherry-evals-postgres"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == "healthy"


@pytest.mark.slow
def test_qdrant_container_healthy(docker_compose_up):
    """Test that Qdrant container is healthy."""
    response = requests.get("http://localhost:6333/healthz", timeout=5)

    assert response.status_code == 200


@pytest.mark.slow
def test_postgres_connection(postgres_connection):
    """Test that we can connect to PostgreSQL."""
    with postgres_connection.connect() as connection:
        result = connection.execute(text("SELECT version()"))
        version = result.fetchone()[0]

        assert "PostgreSQL" in version


@pytest.mark.slow
def test_postgres_database_exists(postgres_connection):
    """Test that the cherry_evals database exists."""
    with postgres_connection.connect() as connection:
        result = connection.execute(text("SELECT current_database()"))
        db_name = result.fetchone()[0]

        assert db_name == "cherry_evals"


@pytest.mark.slow
def test_qdrant_connection(qdrant_connection):
    """Test that we can connect to Qdrant."""
    collections = qdrant_connection.get_collections()

    # Should return a valid response (empty list is ok)
    assert hasattr(collections, "collections")


@pytest.mark.slow
def test_qdrant_health(qdrant_connection):
    """Test Qdrant health endpoint."""
    response = requests.get("http://localhost:6333/healthz", timeout=5)

    assert response.status_code == 200


@pytest.mark.slow
def test_postgres_can_create_table(postgres_connection):
    """Test that we can create and drop tables in PostgreSQL."""
    with postgres_connection.connect() as connection:
        # Create table
        connection.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255)
            )
        """
            )
        )
        connection.commit()

        # Insert data
        connection.execute(text("INSERT INTO test_table (name) VALUES ('test')"))
        connection.commit()

        # Query data
        result = connection.execute(text("SELECT name FROM test_table"))
        name = result.fetchone()[0]

        assert name == "test"

        # Cleanup
        connection.execute(text("DROP TABLE test_table"))
        connection.commit()


@pytest.mark.slow
def test_alembic_migrations_can_run(docker_compose_up):
    """Test that Alembic migrations can run against PostgreSQL."""
    # Run alembic upgrade
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )

    # Check it succeeded
    assert result.returncode == 0

    # Verify tables were created
    from sqlalchemy import create_engine

    engine = create_engine("postgresql://cherry:cherry@localhost:5433/cherry_evals")
    with engine.connect() as connection:
        # Check if alembic_version table exists
        result = connection.execute(
            text(
                """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'alembic_version'
            )
        """
            )
        )
        exists = result.fetchone()[0]

        assert exists is True

    # Downgrade (cleanup)
    subprocess.run(
        ["uv", "run", "alembic", "downgrade", "base"],
        capture_output=True,
        text=True,
    )


@pytest.mark.slow
def test_qdrant_create_collection(qdrant_connection):
    """Test that we can create and delete collections in Qdrant."""
    collection_name = "test_collection"

    # Create collection
    qdrant_connection.create_collection(
        collection_name=collection_name,
        vectors_config={"size": 384, "distance": "Cosine"},
    )

    # Verify it exists
    collections = qdrant_connection.get_collections()
    collection_names = [c.name for c in collections.collections]

    assert collection_name in collection_names

    # Cleanup
    qdrant_connection.delete_collection(collection_name=collection_name)


@pytest.mark.slow
def test_docker_compose_services_running():
    """Test that Docker Compose services are running."""
    result = subprocess.run(
        ["docker", "compose", "ps", "--services", "--filter", "status=running"],
        capture_output=True,
        text=True,
        check=True,
    )

    services = result.stdout.strip().split("\n")

    assert "postgres" in services
    assert "qdrant" in services
