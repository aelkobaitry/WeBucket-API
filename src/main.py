"""Main FastAPI module file with endpoints."""

from typing import Dict

from fastapi import Depends, HTTPException, status
from sqlmodel import Session

from src.auth import get_current_active_user
from src.config import app, get_db_session, init_db, pwd_context
from src.schema import Checklist, Item, User

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


@app.post("/api/v1/create_checklist")
async def create_checklist(
    title: str,
    description: str,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Checklist:
    """Add a new checklist to the database for a user."""
    new_checklist = Checklist(
        title=title,
        description=description,
        owner_id=current_user.id,
        users=[current_user],
    )
    db_session.add(new_checklist)
    db_session.commit()
    db_session.refresh(new_checklist)
    return new_checklist


@app.get("/api/v1/get_checklists_for_user")
async def get_checklists_for_user(
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> list[Checklist]:
    """Get all checklists for a user by username."""
    return current_user.checklists


@app.patch("/api/v1/add_user_to_checklist")
async def add_user_to_checklist(
    checklist_id: str,
    add_user_id: str,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Checklist:
    """Add a user to a checklist by checklist id."""
    checklist = db_session.query(Checklist).filter(Checklist.id == checklist_id).first()
    add_user = db_session.query(User).filter(User.id == add_user_id).first()
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist with id: {checklist_id} not found.",
        )
    if not add_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {add_user_id} not found.",
        )
    if add_user in checklist.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Username: {add_user.username} already in checklist: {checklist.title}.",
        )
    checklist.users.append(add_user)
    db_session.commit()
    db_session.refresh(checklist)
    return checklist


@app.get("/api/v1/checklist/{checklist_id}")
async def get_checklist(
    checklist_id: str,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Checklist:
    """Get all checklist info by checklist id."""
    checklist = db_session.query(Checklist).filter(Checklist.id == checklist_id).first()
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist with id: {checklist_id} not found.",
        )
    return checklist


@app.post("/api/v1/add_item_to_checklist")
async def add_item_to_checklist(
    checklist_id: str,
    title: str,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Item:
    """Add an item to a checklist by checklist id."""
    checklist = db_session.query(Checklist).filter(Checklist.id == checklist_id).first()
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist with id: {checklist_id} not found.",
        )
    new_item = Item(title=title, checklist_id=checklist.id, checklist=checklist)
    db_session.add(new_item)
    db_session.commit()
    db_session.refresh(new_item)
    return new_item


@app.get("/api/v1/get_items_for_checklist")
async def get_items_for_checklist(
    checklist_id: str,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> list[Item]:
    """Get all items for a checklist by checklist id."""
    checklist = db_session.query(Checklist).filter(Checklist.id == checklist_id).first()
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist with id: {checklist_id} not found.",
        )
    return checklist.items
