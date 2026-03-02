"""Shared test fixtures for all test types."""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
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
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_engine):
    """Create a test database session with proper transaction isolation.

    Uses a nested transaction (savepoint) pattern so that endpoint commits
    don't leak data between tests. The outer transaction is always rolled back.
    """
    connection = test_engine.connect()
    transaction = connection.begin()

    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = testing_session_local()

    # When the session calls commit(), only commit the savepoint, not the outer transaction
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def end_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


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
