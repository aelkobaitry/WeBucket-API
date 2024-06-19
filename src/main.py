"""Main FastAPI module file with endpoints."""

from typing import Dict
from uuid import UUID

from auth import get_current_active_user
from config import app, get_db_session, init_db, pwd_context
from fastapi import Depends, HTTPException, status
from schema import Checklist, Item, User
from sqlmodel import Session

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
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get the current logged in user."""
    return current_user


@app.post("/api/v1/add_user")
async def add_user(
    username: str,
    email: str,
    password: str,
    db_session: Session = Depends(get_db_session),
) -> str:
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
    return f"Successfully added new user with username: {username} and email: {email}"


@app.post("/api/v1/create_checklist")
async def create_checklist(
    checklist_title: str,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> str:
    """Add a new checklist to the database for a user by username."""
    checklist = Checklist(title=checklist_title, users=[current_user])
    db_session.add(checklist)
    db_session.commit()
    return f"Successfully added new checklist with title: {checklist.title} and for user: {current_user.username}"


@app.get("/api/v1/get_checklists_for_user")
async def get_checklists_for_user(
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> list[Checklist]:
    """Get all checklists for a user by username."""
    return current_user.checklists


@app.get("/api/v1/add_user_to_checklist")
async def add_user_to_checklist(
    checklist_id: str,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> str:
    """Add a user to a checklist by checklist id."""
    checklist = db_session.query(Checklist).filter(Checklist.id == checklist_id).first()
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist with id: {checklist_id} not found.",
        )
    if current_user in checklist.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Username: {current_user.username} already in checklist: {checklist.title}.",
        )
    checklist.users.append(current_user)
    db_session.commit()
    return f"Successfully added user: {current_user.username} to checklist: {checklist.title}"


@app.get("/api/v1/get_checklist")
async def get_checklist(
    checklist_id: str,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Checklist:
    """Get all checklist info by checklist id."""
    checklist = (
        db_session.query(Checklist).filter(Checklist.id == UUID(checklist_id)).first()
    )
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist with id: {checklist_id} not found.",
        )
    return checklist


@app.get("/api/v1/add_item_to_checklist")
async def add_item_to_checklist(
    checklist_id: str,
    item_title: str,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> str:
    """Add an item to a checklist by checklist id."""
    checklist = (
        db_session.query(Checklist).filter(Checklist.id == UUID(checklist_id)).first()
    )
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist with id: {checklist_id} not found.",
        )
    new_item = Item(title=item_title, checklist_id=checklist.id, checklist=checklist)
    checklist.items.append(new_item)
    db_session.commit()
    return f"Successfully added item: {item_title} to checklist: {checklist.title}"


@app.get("/api/v1/get_items_for_checklist")
async def get_items_for_checklist(
    checklist_id: str,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> list[Item]:
    """Get all items for a checklist by checklist id."""
    checklist = (
        db_session.query(Checklist).filter(Checklist.id == UUID(checklist_id)).first()
    )
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist with id: {checklist_id} not found.",
        )
    return checklist.items
