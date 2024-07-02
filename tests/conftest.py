"""Configs with fixtures for testing."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.config import get_db_session
from src.main import app


@pytest.fixture(name="session")
def session_fixture():
    """Create a new session for each test."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Override the get_session dependency to use the fixture session."""

    def get_session_override():
        """In function to override the get_session dependency."""
        return session

    app.dependency_overrides[get_db_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
