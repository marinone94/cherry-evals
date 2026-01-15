"""Integration test fixtures for database operations."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.postgres.base import Base


@pytest.fixture(scope="function")
def integration_db_engine():
    """Create an in-memory SQLite database for integration tests."""
    from sqlalchemy import event

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    # Enable foreign key support in SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def integration_db_session(integration_db_engine):
    """Create a database session for integration tests."""
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=integration_db_engine)
    session = session_local()
    yield session
    session.close()
