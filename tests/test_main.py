"""Test the main FastAPI app and endpoints."""

from fastapi import status
from fastapi.testclient import TestClient


def test_ping(client: TestClient):
    """Test the ping server endpoint."""
    # Act
    response = client.get("/ping")
    data = response.json()

    assert response.status_code == 200
    assert data == {"ping": "pong"}


def test_add_user_success(client: TestClient):
    """Test the create user endpoint successfully."""
    # Arrange
    payload = {
        "username": "yoda",
        "email": "user@example.com",
        "password": "password123",
    }

    response = client.post("/api/v1/add_user", params=payload)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["username"] == "yoda"
    assert data["email"] == "user@example.com"
    assert data["id"] is not None
    assert data["hashed_password"] is not None
