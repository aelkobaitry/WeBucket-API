"""SQLModel schema for the API."""

import uuid
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel


class UserChecklistLink(SQLModel, table=True):
    """A link table between users and checklists."""

    checklist_id: uuid.UUID = Field(foreign_key="checklist.id", primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)


class User(SQLModel, table=True):
    """A generic user model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str
    email: str
    hashed_password: str
    created_at: datetime = Field(default=datetime.now())
    checklists: list["Checklist"] = Relationship(
        back_populates="users", link_model=UserChecklistLink
    )


class UserUpdate(SQLModel):
    """A generic item model for updating."""

    username: str | None = None
    email: str | None = None
    password: str | None = None


class Checklist(SQLModel, table=True):
    """A generic checklist model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    description: str | None = Field(default=None)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())
    owner_id: uuid.UUID
    users: list[User] = Relationship(
        back_populates="checklists", link_model=UserChecklistLink
    )
    items: list["Item"] = Relationship(back_populates="checklist")


class ChecklistUpdate(SQLModel):
    """A generic checklist model for updating."""

    title: str | None = None
    description: str | None = None


class Item(SQLModel, table=True):
    """A generic item model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    description: str | None = Field(default=None)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())
    checklist_id: uuid.UUID = Field(foreign_key="checklist.id")
    checklist: Checklist = Relationship(back_populates="items")
    rating_user1: int = Field(default=5)
    rating_user2: int = Field(default=5)
    comment_user1: str | None = Field(default=None)
    comment_user2: str | None = Field(default=None)
    complete: bool = Field(default=False)


class ItemUpdate(SQLModel):
    """A generic item model for updating."""

    title: str | None = None
    description: str | None = None
    rating_user1: int | None = None
    rating_user2: int | None = None
    comment_user1: str | None = None
    comment_user2: str | None = None
    complete: bool | None = None
