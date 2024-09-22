"""Test the main FastAPI app and endpoints."""

from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.schema import Bucket, Item, ItemType, User


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
        "firstname": "Chew",
        "lastname": "Bacca",
        "username": "chewbacca",
        "email": "chewy@example.com",
        "password": "password123",
    }

    # Act
    response = client.post("/api/v1/add_user", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert data["firstname"] == payload["firstname"]
    assert data["lastname"] == payload["lastname"]
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
    assert added_user.firstname == payload["firstname"]
    assert added_user.lastname == payload["lastname"]
    assert added_user.username == payload["username"]
    assert added_user.email == payload["email"]
    assert added_user.hashed_password is not None


def test_add_user_same_username(client: TestClient, session: Session):
    """Test the create user endpoint with a previously used username."""
    # Arrange
    payload = {
        "firstname": "Yoda",
        "lastname": "Master",
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
        "firstname": "Not",
        "lastname": "Yoda",
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


def test_add_bucket_success(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the create bucket endpoint successfully."""
    # Arrange
    payload = {
        "title": "My Bucket",
        "description": "A general description.",
    }

    # Act
    response = client.post("/api/v1/create_bucket", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 2
    assert data[1]["title"] == payload["title"]
    assert data[1]["description"] == payload["description"]
    assert data[1]["id"] is not None
    assert data[1]["owner_id"] == str(two_users[0].id)

    assert len(two_users[0].buckets) == 2

    added_bucket = session.query(Bucket).filter(Bucket.id == data[1]["id"]).first()
    assert str(added_bucket.id) == data[1]["id"]
    assert added_bucket.title == payload["title"]
    assert added_bucket.description == payload["description"]
    assert added_bucket.owner_id == two_users[0].id
    assert str(added_bucket.owner_id) == data[1]["owner_id"]


def test_add_bucket_empty_title(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the create bucket endpoint with an empty title."""
    # Arrange
    payload = {
        "title": "",
        "description": "A general description.",
    }

    # Act
    response = client.post("/api/v1/create_bucket", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["detail"] == "Bucket title cannot be empty."


def test_add_bucket_long_title(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the create bucket endpoint with a long title."""
    # Arrange
    payload = {
        "title": "A" * 51,
        "description": "A general description.",
    }

    # Act
    response = client.post("/api/v1/create_bucket", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["detail"] == "Bucket title cannot exceed 50 characters."


def test_get_buckets_for_user(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the get buckets for user endpoint successfully."""
    # Act
    response = client.get("/api/v1/get_buckets_for_user")
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 1
    assert data[0]["title"] == "First Bucket"
    assert data[0]["description"] == "Generic description"
    assert data[0]["owner_id"] == str(two_users[0].id)


def test_add_user_to_bucket(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the add user to bucket endpoint successfully."""
    # Arrange
    bucket_id = two_users[0].buckets[0].id
    payload = {"bucket_id": bucket_id, "add_username": two_users[1].username}

    # Act
    response = client.patch("/api/v1/add_user_to_bucket", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 2
    assert str(two_users[0].username), str(two_users[1].username) in [
        user["username"] for user in data
    ]

    bucket = session.query(Bucket).filter(Bucket.id == bucket_id).first()
    assert len(bucket.users) == 2
    assert two_users[0].username, two_users[1].username in [
        user.username for user in bucket.users
    ]

    assert len(two_users[0].buckets) == 1
    assert len(two_users[1].buckets) == 1


def test_add_user_bucket_not_existing(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the add user to bucket endpoint with a non-existing bucket."""
    # Arrange
    bucket_id = "12345678-1234-1234-1234-123456789abc"
    payload = {"bucket_id": bucket_id, "add_username": str(two_users[1].username)}

    # Act
    response = client.patch("/api/v1/add_user_to_bucket", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == f"Bucket with id: {bucket_id} not found."


def test_add_user_not_existing(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the add user to bucket endpoint with a non-existing user."""
    # Arrange
    bucket_id = two_users[0].buckets[0].id
    bad_username = "thisusernamedoesnotexist"
    payload = {"bucket_id": bucket_id, "add_username": bad_username}

    # Act
    response = client.patch("/api/v1/add_user_to_bucket", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == f"User with username: {bad_username} not found."


def test_add_user_to_bucket_already_added(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the add user to bucket endpoint with a user already added."""
    # Arrange
    bucket_id = two_users[0].buckets[0].id
    payload = {"bucket_id": bucket_id, "add_username": two_users[0].username}

    # Act
    response = client.patch("/api/v1/add_user_to_bucket", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert (
        data["detail"]
        == f"Username: {two_users[0].username} already in bucket: {two_users[0].buckets[0].title}."
    )


def test_get_bucket_successfully(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the get bucket endpoint successfully."""
    # Arrange
    bucket_id = two_users[0].buckets[0].id

    item1 = Item(
        title="firstItem",
        description="testing first item",
        item_type=ItemType.activity,
        bucket_id=bucket_id,
    )

    item2 = Item(
        title="secondItem",
        description="testing second item",
        item_type=ItemType.media,
        bucket_id=bucket_id,
    )

    item3 = Item(
        title="thirdItem",
        description="testing third item",
        item_type=ItemType.food,
        bucket_id=bucket_id,
    )
    session.add_all([item1, item2, item3])
    session.commit()

    # Act
    response = client.get(f"/api/v1/bucket/{bucket_id}")
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert data["bucket"]["title"] == "First Bucket"
    assert data["bucket"]["description"] == "Generic description"
    assert data["bucket"]["owner_id"] == str(two_users[0].id)
    assert len(data["activity"]) == 2
    assert len(data["media"]) == 1
    assert len(data["food"]) == 1


def test_get_bucket_not_existing(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the get bucket endpoint with a non-existing bucket."""
    # Arrange
    bucket_id = "12345678-1234-1234-1234-123456789abc"

    # Act
    response = client.get(f"/api/v1/bucket/{bucket_id}")
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == f"Bucket with id: {bucket_id} not found."


def test_delete_bucket_successfully(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the delete bucket endpoint successfully."""
    # Arrange
    bucket_id = two_users[0].buckets[0].id
    item_id = two_users[0].buckets[0].items[0].id
    # Act
    response = client.delete(f"/api/v1/delete_bucket/{bucket_id}")
    data = response.json()
    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 0

    bucket = session.query(Bucket).filter(Bucket.id == bucket_id).first()
    assert bucket is None
    item = session.query(Item).filter(Item.id == item_id).first()
    assert item is None


def test_delete_bucket_not_exist(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the delete bucket endpoint where bucket does not exist."""
    # Arrange
    bucket_id = "12345678-1234-1234-1234-123456789abc"
    # Act
    response = client.delete(f"/api/v1/delete_bucket/{bucket_id}")
    data = response.json()
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == f"Bucket with id: {bucket_id} not found."


def test_add_item_to_bucket_successfully(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the add item to bucket endpoint successfully."""
    # Arrange
    bucket_id = str(two_users[0].buckets[0].id)
    payload = {"bucket_id": bucket_id, "title": "First Item", "item_type": "activity"}

    # Act
    response = client.post("/api/v1/add_item_to_bucket", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert data["title"] == payload["title"]
    assert data["bucket_id"] == bucket_id
    assert data["item_type"] == payload["item_type"]
    assert data["description"] is None
    assert data["rating_user1"] == 5
    assert data["rating_user2"] == 5
    assert data["complete"] is False

    added_item = session.query(Item).filter(Item.id == data["id"]).first()
    assert added_item is not None
    assert str(added_item.id) == data["id"]
    assert added_item.title == payload["title"]
    assert str(added_item.bucket_id) == bucket_id
    assert added_item.item_type == payload["item_type"]
    assert added_item.description is None
    assert added_item.rating_user1 == 5
    assert added_item.rating_user2 == 5
    assert added_item.complete is False


def test_add_item_to_bucket_not_existing(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test the add item to bucket endpoint with a non-existing bucket."""
    # Arrange
    bucket_id = "12345678-1234-1234-1234-123456789abc"
    payload = {"bucket_id": bucket_id, "title": "First Item", "item_type": "activity"}

    # Act
    response = client.post("/api/v1/add_item_to_bucket", params=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == f"Bucket with id: {bucket_id} not found."


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
    bucket = two_users[0].buckets[0]
    item_id = str(two_users[0].buckets[0].items[0].id)
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
    assert database_item.bucket_id == bucket.id


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
        "firstname": "Updated",
        "lastname": "Yoda",
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
    assert data["firstname"] == payload["firstname"]
    assert data["lastname"] == payload["lastname"]
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert data["hashed_password"] is not None

    database_user = session.query(User).filter(User.id == user_id).first()
    assert str(database_user.id) == data["id"]
    assert database_user.firstname == payload["firstname"]
    assert database_user.lastname == payload["lastname"]
    assert database_user.username == payload["username"]
    assert database_user.email == payload["email"]
    assert database_user.hashed_password is not None


def test_update_bucket_not_existing(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test update bucket endpoint with a non-existing bucket."""
    # Arrange
    bucket_id = "12345678-1234-1234-1234-123456789abc"
    payload = {
        "title": "Nonexistent Bucket Title",
        "description": "Trying to update a non-existent bucket.",
    }

    query = {
        "bucket_id": bucket_id,
    }

    # Act
    response = client.patch("/api/v1/update_bucket", params=query, json=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == f"Bucket with id: {bucket_id} not found."


def test_update_bucket_succesfully(
    client: TestClient, session: Session, two_users: tuple[User, User]
):
    """Test update bucket endpoint successfully."""
    # Arrange
    bucket_id = str(two_users[0].buckets[0].id)
    original_updated_at = two_users[0].buckets[0].updated_at
    payload = {
        "title": "Updated Bucket Title",
        "description": "Updated description of the bucket.",
        "bookmark": True,
    }

    query = {
        "bucket_id": bucket_id,
    }

    # Act
    response = client.patch("/api/v1/update_bucket", params=query, json=payload)
    data = response.json()

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert data[0]["id"] == bucket_id
    assert data[0]["title"] == payload["title"]
    assert data[0]["description"] == payload["description"]
    assert data[0]["bookmark"] == payload["bookmark"]

    database_bucket = session.query(Bucket).filter(Bucket.id == bucket_id).first()
    assert str(database_bucket.id) == data[0]["id"]
    assert database_bucket.title == payload["title"]
    assert database_bucket.description == payload["description"]
    assert database_bucket.bookmark == payload["bookmark"]
    assert database_bucket.updated_at > original_updated_at
    assert database_bucket.owner_id == two_users[0].id
