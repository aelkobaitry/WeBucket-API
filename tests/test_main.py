"""Test the main FastAPI app and endpoints."""

from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.schema import Checklist, User


def test_ping(client: TestClient):
    """Test the ping server endpoint."""
    # Act
    response = client.get("/ping")
    data = response.json()

    assert response.status_code == 200
    assert data == {"ping": "pong"}


def test_add_user_success(client: TestClient, session: Session):
    """Test the create user endpoint successfully."""
    # Arrange
    payload = {
        "username": "chewbacca",
        "email": "chewy@example.com",
        "password": "password123",
    }

    # Act
    response = client.post("/api/v1/add_user", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert data["id"] is not None
    assert data["hashed_password"] is not None

    all_users = session.query(User).all()
    assert len(all_users) == 3

    added_user = (
        session.query(User).filter(User.username == payload["username"]).first()
    )
    assert str(added_user.id) == data["id"]
    assert added_user.username == payload["username"]
    assert added_user.email == payload["email"]
    assert added_user.hashed_password is not None


def test_add_user_same_username(client: TestClient, session: Session):
    """Test the create user endpoint with a previously used username."""
    # Arrange
    payload = {
        "username": "yoda",
        "email": "notuser@example.com",
        "password": "password123",
    }

    # Act
    response = client.post("/api/v1/add_user", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        data["detail"] == f"User with username: {payload['username']} already exists."
    )
    all_users = session.query(User).all()
    assert len(all_users) == 2


def test_add_user_same_email(client: TestClient, two_users: tuple[User, User]):
    """Test the create user endpoint with a previously used email."""
    # Arrange
    payload = {
        "username": "notyoda",
        "email": "user@example.com",
        "password": "password123",
    }

    # Act
    response = client.post("/api/v1/add_user", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["detail"] == f"User with email: {payload['email']} already exists."


def test_add_checklist_success(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the create checklist endpoint successfully."""
    # Arrange
    payload = {"title": "My Checklist", "description": "A general description."}

    # Act
    response = client.post("/api/v1/create_checklist", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    print(data)
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["id"] is not None
    assert data["owner_id"] == str(two_users[0].id)

    assert len(two_users[0].checklists) == 2

    added_checklist = (
        session.query(Checklist).filter(Checklist.id == data["id"]).first()
    )
    assert str(added_checklist.id) == data["id"]
    assert added_checklist.title == payload["title"]
    assert added_checklist.description == payload["description"]
    assert added_checklist.owner_id == two_users[0].id
    assert str(added_checklist.owner_id) == data["owner_id"]


def test_get_checklists_for_user(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the get checklists for user endpoint successfully."""
    # Act
    response = client.get("/api/v1/get_checklists_for_user")
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 1
    assert data[0]["title"] == "First Checklist"
    assert data[0]["description"] == "Generic description"
    assert data[0]["owner_id"] == str(two_users[0].id)


def test_add_user_to_checklist(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the add user to checklist endpoint successfully."""
    # Arrange
    checklist_id = two_users[0].checklists[0].id
    payload = {"checklist_id": checklist_id, "add_user_id": two_users[1].id}

    # Act
    response = client.patch("/api/v1/add_user_to_checklist", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert data["id"] == str(checklist_id)

    checklist = session.query(Checklist).filter(Checklist.id == checklist_id).first()
    assert len(checklist.users) == 2
    assert checklist.users[1].id == two_users[1].id

    assert len(two_users[1].checklists) == 1
