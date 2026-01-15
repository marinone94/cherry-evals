"""Shared test fixtures for all test types."""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.main import app
from cherry_evals.config import Settings
from db.postgres.base import Base, get_db


@pytest.fixture(scope="session")
def test_settings():
    """Create test settings with overridden values."""
    return Settings(
        database_url="sqlite:///./test.db",
        qdrant_url="http://localhost:6333",
        google_api_key="test-api-key",
        cherry_data_dir=Path("./test_data"),
    )


@pytest.fixture(scope="session")
def test_engine(test_settings):
    """Create a test database engine."""
    engine = create_engine(
        test_settings.database_url,
        connect_args={"check_same_thread": False},  # Needed for SQLite
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_engine):
    """Create a test database session with transaction rollback."""
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = testing_session_local()

    yield session

    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def test_client(test_db_session):
    """Create a FastAPI test client with test database."""

    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """Set test environment variables."""
    os.environ["TESTING"] = "1"
    yield
    os.environ.pop("TESTING", None)
