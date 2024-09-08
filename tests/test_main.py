"""Test the main FastAPI app and endpoints."""

from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.schema import Checklist, Item, User


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
    payload = {
        "title": "My Checklist",
        "description": "A general description.",
        "checklist_type": "activity",
    }

    # Act
    response = client.post("/api/v1/create_checklist", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    print(data)
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["checklist_type"] == payload["checklist_type"]
    assert data["id"] is not None
    assert data["owner_id"] == str(two_users[0].id)

    assert len(two_users[0].checklists) == 2

    added_checklist = (
        session.query(Checklist).filter(Checklist.id == data["id"]).first()
    )
    assert str(added_checklist.id) == data["id"]
    assert added_checklist.title == payload["title"]
    assert added_checklist.description == payload["description"]
    assert added_checklist.checklist_type == payload["checklist_type"]
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
    assert data[0]["checklist_type"] == "activity"
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
    assert two_users[0].id, two_users[1].id in [user.id for user in checklist.users]

    assert len(two_users[0].checklists) == 1
    assert len(two_users[1].checklists) == 1


def test_add_user_checklist_not_existing(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the add user to checklist endpoint with a non-existing checklist."""
    # Arrange
    checklist_id = "12345678-1234-1234-1234-123456789abc"
    payload = {"checklist_id": checklist_id, "add_user_id": str(two_users[1].id)}

    # Act
    response = client.patch("/api/v1/add_user_to_checklist", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == f"Checklist with id: {checklist_id} not found."


def test_add_user_not_existing(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the add user to checklist endpoint with a non-existing user."""
    # Arrange
    checklist_id = two_users[0].checklists[0].id
    bad_user_id = "12345678-1234-1234-1234-123456789abc"
    payload = {"checklist_id": checklist_id, "add_user_id": bad_user_id}

    # Act
    response = client.patch("/api/v1/add_user_to_checklist", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == f"User with id: {bad_user_id} not found."


def test_add_user_to_checklist_already_added(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the add user to checklist endpoint with a user already added."""
    # Arrange
    checklist_id = two_users[0].checklists[0].id
    payload = {"checklist_id": checklist_id, "add_user_id": two_users[0].id}

    # Act
    response = client.patch("/api/v1/add_user_to_checklist", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert (
        data["detail"]
        == f"Username: {two_users[0].username} already in checklist: {two_users[0].checklists[0].title}."
    )


def test_get_checklist_successfully(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the get checklist endpoint successfully."""
    # Arrange
    checklist_id = two_users[0].checklists[0].id

    # Act
    response = client.get(f"/api/v1/checklist/{checklist_id}")
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert data["title"] == "First Checklist"
    assert data["description"] == "Generic description"
    assert data["owner_id"] == str(two_users[0].id)


def test_get_checklist_not_existing(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the get checklist endpoint with a non-existing checklist."""
    # Arrange
    checklist_id = "12345678-1234-1234-1234-123456789abc"

    # Act
    response = client.get(f"/api/v1/checklist/{checklist_id}")
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == f"Checklist with id: {checklist_id} not found."


def test_add_item_to_checklist_successfully(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the add item to checklist endpoint successfully."""
    # Arrange
    checklist_id = str(two_users[0].checklists[0].id)
    payload = {"checklist_id": checklist_id, "title": "First Item"}

    # Act
    response = client.post("/api/v1/add_item_to_checklist", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert data["title"] == "First Item"
    assert data["checklist_id"] == checklist_id
    assert data["description"] is None
    assert data["rating_user1"] == 5
    assert data["rating_user2"] == 5
    assert data["complete"] is False


def test_add_item_to_checklist_not_existing(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the add item to checklist endpoint with a non-existing checklist."""
    # Arrange
    checklist_id = "12345678-1234-1234-1234-123456789abc"
    payload = {"checklist_id": checklist_id, "title": "First Item"}

    # Act
    response = client.post("/api/v1/add_item_to_checklist", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == f"Checklist with id: {checklist_id} not found."


def test_get_items_in_checklist_successfully(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the get items in checklist endpoint successfully."""
    # Arrange
    checklist_id = two_users[0].checklists[0].id

    item = Item(
        title="First Item",
        checklist_id=checklist_id,
        description=None,
        rating_user1=5,
        rating_user2=5,
        complete=False,
    )

    session.add(item)
    session.commit()
    session.refresh(item)

    payload = {"checklist_id": checklist_id}

    # Act
    response = client.get("/api/v1/get_items_for_checklist", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 2
    assert data[1]["title"] == "First Item"
    assert data[1]["checklist_id"] == str(checklist_id)
    assert data[1]["description"] is None
    assert data[1]["rating_user1"] == 5
    assert data[1]["rating_user2"] == 5
    assert data[1]["complete"] is False


def test_update_item_not_existing(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test update item endpoint with a non-existing item."""
    # Arrange
    item_id = "12345678-1234-1234-1234-123456789abc"
    payload = {"title": "First item change", "description": "changing the description."}

    query = {
        "item_id": item_id,
    }

    # Act
    response = client.patch("/api/v1/update_item", params=query, json=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == f"Item with id: {item_id} not found."


def test_update_item_successfully(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test update item endpoint successfully."""
    # Arrange
    checklist = two_users[0].checklists[0]
    item_id = str(two_users[0].checklists[0].items[0].id)
    payload = {"title": "First item change", "description": "changing the description."}

    query = {
        "item_id": item_id,
    }

    # Act
    response = client.patch("/api/v1/update_item", params=query, json=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert data["id"] == str(item_id)
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]

    database_item = session.query(Item).filter(Item.id == item_id).first()
    assert str(database_item.id) == data["id"]
    assert database_item.title == payload["title"]
    assert database_item.description == payload["description"]
    assert database_item.checklist_id == checklist.id


def test_update_user_not_existing(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test update user endpoint with a non-existing user."""
    # Arrange
    user_id = "12345678-1234-1234-1234-123456789abc"
    payload = {"username": "nonexistent_user", "email": "nonexistent_user@example.com"}

    query = {
        "user_id": user_id,
    }

    # Act
    response = client.patch("/api/v1/update_user", params=query, json=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == f"User with id: {user_id} not found."


def test_update_user_successfully(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test update user endpoint successfully."""
    # Arrange
    user_id = str(two_users[0].id)
    payload = {
        "username": "updated_yoda",
        "email": "updated_yoda@example.com",
        "hashed_password": "newpassword123",
    }

    query = {
        "user_id": user_id,
    }

    # Act
    response = client.patch("/api/v1/update_user", params=query, json=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert data["id"] == user_id
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert data["hashed_password"] is not None

    database_user = session.query(User).filter(User.id == user_id).first()
    assert str(database_user.id) == data["id"]
    assert database_user.username == payload["username"]
    assert database_user.email == payload["email"]
    assert database_user.hashed_password is not None


def test_update_checklist_not_existing(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test update checklist endpoint with a non-existing checklist."""
    # Arrange
    checklist_id = "12345678-1234-1234-1234-123456789abc"
    payload = {
        "title": "Nonexistent Checklist Title",
        "description": "Trying to update a non-existent checklist.",
    }

    query = {
        "checklist_id": checklist_id,
    }

    # Act
    response = client.patch("/api/v1/update_checklist", params=query, json=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == f"Checklist with id: {checklist_id} not found."


def test_update_checklist_succesfully(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test update checklist endpoint successfully."""
    # Arrange
    checklist_id = str(two_users[0].checklists[0].id)
    original_updated_at = two_users[0].checklists[0].updated_at
    payload = {
        "title": "Updated Checklist Title",
        "description": "Updated description of the checklist.",
    }

    query = {
        "checklist_id": checklist_id,
    }

    # Act
    response = client.patch("/api/v1/update_checklist", params=query, json=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert data["id"] == checklist_id
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]

    database_checklist = (
        session.query(Checklist).filter(Checklist.id == checklist_id).first()
    )
    assert str(database_checklist.id) == data["id"]
    assert database_checklist.title == payload["title"]
    assert database_checklist.description == payload["description"]
    assert database_checklist.updated_at > original_updated_at
    assert database_checklist.owner_id == two_users[0].id
