"""Main FastAPI module file with endpoints."""

from datetime import datetime
from typing import Dict

from fastapi import Depends, HTTPException, status
from sqlmodel import Session

from src.auth import get_current_active_user
from src.config import app, get_db_session, init_db, pwd_context
from src.schema import (
    Bucket,
    BucketUpdate,
    Item,
    ItemType,
    ItemUpdate,
    User,
    UserUpdate,
)

# fastapi dev main.py


@app.on_event("startup")
async def startup_event():
    """Create the database tables on startup."""
    init_db()


@app.get("/")
async def root():
    """Root endpoint."""
    return {"Hello": "World"}


@app.get("/ping")
async def ping() -> Dict[str, str]:
    """Ping endpoint for error testing."""
    return {"ping": "pong"}


@app.get("/api/v1/auth/current_user", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)) -> User:
    """Get the current logged in user."""
    return current_user


@app.post("/api/v1/add_user")
async def add_user(
    username: str,
    email: str,
    password: str,
    db_session: Session = Depends(get_db_session),
) -> User:
    """Add a new user to the database."""
    if db_session.query(User).filter(User.username == username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with username: {username} already exists.",
        )
    if db_session.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email: {email} already exists.",
        )
    new_user = User(
        username=username, email=email, hashed_password=pwd_context.hash(password)
    )
    db_session.add(new_user)
    db_session.commit()
    db_session.refresh(new_user)
    return new_user


@app.post("/api/v1/create_bucket")
async def create_bucket(
    title: str,
    description: str,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> list[Bucket]:
    """Add a new bucket to the database for a user."""
    new_bucket = Bucket(
        title=title,
        description=description,
        owner_id=current_user.id,
        users=[current_user],
    )
    db_session.add(new_bucket)
    db_session.commit()
    db_session.refresh(new_bucket)
    return current_user.buckets


@app.get("/api/v1/get_buckets_for_user")
async def get_buckets_for_user(
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> list[Bucket]:
    """Get all buckets for a user by username."""
    return current_user.buckets


@app.patch("/api/v1/add_user_to_bucket")
async def add_user_to_bucket(
    bucket_id: str,
    add_username: str,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> list[User]:
    """Add a user to a bucket by bucket id."""
    bucket = db_session.query(Bucket).filter(Bucket.id == bucket_id).first()
    add_user = db_session.query(User).filter(User.username == add_username).first()
    if not bucket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bucket with id: {bucket_id} not found.",
        )
    if not add_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username: {add_username} not found.",
        )
    if add_user in bucket.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Username: {add_user.username} already in bucket: {bucket.title}.",
        )
    bucket.users.append(add_user)
    db_session.commit()
    db_session.refresh(bucket)
    return bucket.users


@app.get("/api/v1/bucket/{bucket_id}")
async def get_bucket(
    bucket_id: str,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Get all bucket info by bucket id."""
    bucket = db_session.query(Bucket).filter(Bucket.id == bucket_id).first()
    if not bucket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bucket with id: {bucket_id} not found.",
        )
    if current_user not in bucket.users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User: {current_user.username} not in bucket: {bucket.title}.",
        )

    activity = [item for item in bucket.items if item.item_type == ItemType.activity]
    media = [item for item in bucket.items if item.item_type == ItemType.media]
    food = [item for item in bucket.items if item.item_type == ItemType.food]

    return {"activity": activity, "media": media, "food": food, "bucket": bucket}


@app.delete("/api/v1/delete_bucket/{bucket_id}")
async def delete_bucket(
    bucket_id: str,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> list[Bucket]:
    """Delete a bucket by bucket id."""
    bucket = db_session.query(Bucket).filter(Bucket.id == bucket_id).first()
    if not bucket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bucket with id: {bucket_id} not found.",
        )
    if bucket.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User: {current_user.username} not authorized to delete bucket: {bucket.title}.",
        )
    for item in bucket.items:
        db_session.delete(item)
    db_session.delete(bucket)
    db_session.commit()
    db_session.refresh(current_user)
    return current_user.buckets


@app.post("/api/v1/add_item_to_bucket")
async def add_item_to_bucket(
    bucket_id: str,
    title: str,
    item_type: ItemType,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Item:
    """Add an item to a bucket by bucket id."""
    bucket = db_session.query(Bucket).filter(Bucket.id == bucket_id).first()
    if not bucket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bucket with id: {bucket_id} not found.",
        )
    if current_user not in bucket.users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User: {current_user.username} not in bucket: {bucket.title}.",
        )
    new_item = Item(
        title=title, bucket_id=bucket.id, bucket=bucket, item_type=item_type
    )
    db_session.add(new_item)
    db_session.commit()
    db_session.refresh(new_item)
    return new_item


@app.patch("/api/v1/update_item")
async def update_item(
    item_id: str,
    item_update: ItemUpdate,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Item:
    """Update an item with optional fields."""
    db_item = db_session.get(Item, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id: {item_id} not found.",
        )
    item_data = item_update.model_dump(exclude_unset=True)
    db_item.sqlmodel_update(item_data)
    db_session.add(db_item)
    db_session.commit()
    db_session.refresh(db_item)
    return db_item


@app.patch("/api/v1/update_user")
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Update a user with optional fields."""
    db_user = db_session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {user_id} not found.",
        )
    user_data = user_update.model_dump(exclude_unset=True)
    if "password" in user_data:
        user_data["hashed_password"] = pwd_context.hash(user_data.pop("password"))
    db_user.sqlmodel_update(user_data)
    db_session.add(db_user)
    db_session.commit()
    db_session.refresh(db_user)
    return db_user


@app.patch("/api/v1/update_bucket")
async def update_bucket(
    bucket_id: str,
    bucket_update: BucketUpdate,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Bucket:
    """Update a bucket with optional fields."""
    db_bucket = db_session.get(Bucket, bucket_id)
    if not db_bucket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bucket with id: {bucket_id} not found.",
        )
    bucket_data = bucket_update.model_dump(exclude_unset=True)
    db_bucket.sqlmodel_update(bucket_data)
    db_bucket.updated_at = datetime.now()
    db_session.add(db_bucket)
    db_session.commit()
    db_session.refresh(db_bucket)
    return db_bucket
