"""Configs with fixtures for testing."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.auth import get_current_active_user
from src.config import get_db_session
from src.main import app
from src.schema import Checklist, Item, User


@pytest.fixture(name="session")
def session_fixture() -> Session:
    """Create a new session for each test."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="two_users")
def add_two_users(session: Session) -> tuple[User, User]:
    """Adds two users to the database."""
    user1 = User(
        username="yoda", email="user@example.com", hashed_password="password123"
    )
    user2 = User(
        username="vader", email="user2@example.com", hashed_password="password"
    )
    session.add(user1)
    session.add(user2)
    session.commit()
    checklist1 = Checklist(
        title="First Checklist",
        description="Generic description",
        owner_id=user1.id,
        users=[user1],
    )
    session.add(checklist1)
    session.commit()
    session.refresh(user1)
    item1 = Item(
        title="firstItem",
        description="testing first item",
        checklist=checklist1,
        checklist_id=checklist1.id,
    )
    session.add(item1)
    session.commit()
    session.refresh(checklist1)
    return user1, user2


@pytest.fixture(name="client")
def client_fixture(session: Session, two_users: tuple[User, User]) -> TestClient:
    """Override the get_session dependency to use the fixture session."""

    def get_session_override():
        """In function to override the get_session dependency."""
        return session

    def get_current_active_user_override():
        """In function to override the get_current_user dependency."""
        return two_users[0]

    app.dependency_overrides[get_db_session] = get_session_override
    app.dependency_overrides[get_current_active_user] = get_current_active_user_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
