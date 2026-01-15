"""System test fixtures for Docker Compose infrastructure."""

import subprocess
import time

import pytest
import requests
from qdrant_client import QdrantClient
from sqlalchemy import create_engine, text


@pytest.fixture(scope="module")
def docker_compose_up():
    """Start Docker Compose services for system tests."""
    # Start docker compose (v2)
    subprocess.run(["docker", "compose", "up", "-d"], check=True)

    # Wait for services to be healthy
    max_retries = 30
    retry_delay = 2

    # Wait for PostgreSQL
    for i in range(max_retries):
        result = subprocess.run(
            ["docker", "inspect", "--format={{.State.Health.Status}}", "cherry-evals-postgres"],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip() == "healthy":
            break
        time.sleep(retry_delay)
    else:
        raise TimeoutError("PostgreSQL container did not become healthy")

    # Wait for Qdrant
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:6333/healthz", timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(retry_delay)
    else:
        raise TimeoutError("Qdrant container did not become healthy")

    yield

    # Cleanup
    subprocess.run(["docker", "compose", "down", "-v"], check=False)


@pytest.fixture(scope="function")
def postgres_connection(docker_compose_up):
    """Provide a PostgreSQL connection for system tests."""
    engine = create_engine("postgresql://cherry:cherry@localhost:5433/cherry_evals")

    # Test connection
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    yield engine

    engine.dispose()


@pytest.fixture(scope="function")
def qdrant_connection(docker_compose_up):
    """Provide a Qdrant client for system tests."""
    client = QdrantClient(url="http://localhost:6333")

    # Test connection
    client.get_collections()

    yield client


def wait_for_service(host: str, port: int, timeout: int = 30) -> bool:
    """Wait for a service to be available."""
    import socket

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False
