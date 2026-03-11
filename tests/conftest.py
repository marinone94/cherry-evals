"""Shared test fixtures for all test types."""

import os
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from api.deps import get_current_user, get_optional_user
from api.main import app
from cherry_evals.config import Settings
from db.postgres.base import Base, get_db
from db.postgres.models import User


@pytest.fixture(scope="session")
def test_settings():
    """Create test settings with overridden values."""
    return Settings(
        database_url="sqlite:///./test.db",
        qdrant_url="http://localhost:6333",
        google_api_key="test-api-key",
        cherry_data_dir=Path("./test_data"),
        auth_enabled=False,
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
def test_client(test_db_session, test_settings):
    """Create a FastAPI test client with test database and auth disabled."""

    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with (
        patch("api.deps.settings", test_settings),
        patch("api.routes.export.settings", test_settings),
        patch("api.routes.collections.settings", test_settings),
        TestClient(app) as client,
    ):
        yield client

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth test helpers
# ---------------------------------------------------------------------------


def _make_fake_user(
    *, tier: str = "free", supabase_id: str = "test-user-123", trial_ends_at=None
) -> User:
    """Build an in-memory User object for dependency overrides."""
    from datetime import UTC, datetime, timedelta

    return User(
        id=1,
        supabase_id=supabase_id,
        email=f"{tier}@test.com",
        tier=tier,
        trial_ends_at=trial_ends_at,
        polar_customer_id=None,
        polar_subscription_id=None,
        subscription_status=None,
        llm_calls_today=0,
        semantic_searches_today=0,
        quota_reset_at=datetime.now(UTC) + timedelta(days=1),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def free_user():
    """A Free-tier User object."""
    return _make_fake_user(tier="free")


@pytest.fixture
def pro_user():
    """A Pro-tier User object."""
    return _make_fake_user(tier="pro", supabase_id="pro-user-456")


@pytest.fixture
def ultra_user():
    """An Ultra-tier User object."""
    return _make_fake_user(tier="ultra", supabase_id="ultra-user-789")


@pytest.fixture
def trial_user():
    """A Free-tier user with an active Ultra trial."""
    from datetime import UTC, datetime, timedelta

    return _make_fake_user(
        tier="free",
        supabase_id="trial-user-101",
        trial_ends_at=datetime.now(UTC) + timedelta(days=7),
    )


@pytest.fixture
def expired_trial_user():
    """A Free-tier user with an expired trial."""
    from datetime import UTC, datetime, timedelta

    return _make_fake_user(
        tier="free",
        supabase_id="expired-trial-user-102",
        trial_ends_at=datetime.now(UTC) - timedelta(days=1),
    )


# ---------------------------------------------------------------------------
# Authenticated test client factory
# ---------------------------------------------------------------------------


def _make_authed_client(test_db_session, user):
    """Create a test client authenticated as the given user.

    Patches settings across all route modules that reference them directly.
    """
    authed_settings = Settings(
        database_url="sqlite:///./test.db",
        qdrant_url="http://localhost:6333",
        google_api_key="test-api-key",
        cherry_data_dir=Path("./test_data"),
        auth_enabled=True,
        supabase_jwt_secret="test-secret",
    )

    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    def override_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_optional_user] = override_user

    @contextmanager
    def _client_context():
        with (
            patch("api.deps.settings", authed_settings),
            patch("api.routes.export.settings", authed_settings),
            patch("api.routes.collections.settings", authed_settings),
            TestClient(app) as client,
        ):
            yield client
        app.dependency_overrides.clear()

    return _client_context()


@pytest.fixture
def authed_client_free(test_db_session, free_user):
    """Test client authenticated as a Free user (auth_enabled=True)."""
    with _make_authed_client(test_db_session, free_user) as client:
        yield client


@pytest.fixture
def authed_client_pro(test_db_session, pro_user):
    """Test client authenticated as a Pro user (auth_enabled=True)."""
    with _make_authed_client(test_db_session, pro_user) as client:
        yield client


@pytest.fixture
def authed_client_ultra(test_db_session, ultra_user):
    """Test client authenticated as an Ultra user (auth_enabled=True)."""
    with _make_authed_client(test_db_session, ultra_user) as client:
        yield client


@pytest.fixture
def authed_client_trial(test_db_session, trial_user):
    """Test client authenticated as a Free user with active Ultra trial."""
    with _make_authed_client(test_db_session, trial_user) as client:
        yield client


@pytest.fixture
def authed_client_expired_trial(test_db_session, expired_trial_user):
    """Test client authenticated as a Free user with expired trial."""
    with _make_authed_client(test_db_session, expired_trial_user) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """Set test environment variables."""
    os.environ["TESTING"] = "1"
    yield
    os.environ.pop("TESTING", None)
