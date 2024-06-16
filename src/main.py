"""Main FastAPI module file with endpoints."""

from pathlib import Path
from typing import Dict
from uuid import UUID

from config import Settings
from fastapi import Depends, FastAPI, HTTPException
from schema import Checklist, Item, User
from sqlalchemy.orm import Session
from sqlmodel import SQLModel, create_engine

# fastapi dev main.py


source_config = Path("config.toml")

config = {"database": {"url": "sqlite:///database_service/db.sqlite"}}

engine = create_engine(
    config["database"]["url"], echo=True, connect_args={"check_same_thread": False}
)

app = FastAPI(title=Settings.PROJECT_NAME, version=Settings.PROJECT_VERSION)


def get_db_session() -> Session:
    """Make a new database session for each request."""
    with Session(engine) as session:
        yield session


@app.on_event("startup")
async def startup_event():
    """Create the database tables on startup."""
    print("Starting up...")
    SQLModel.metadata.create_all(engine)
    print(f"Project name: {Settings.PROJECT_NAME}")
    print(f"Project version: {Settings.PROJECT_VERSION}")
    print(f"Database URL: {config['database']['url']}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"Hello": "World"}


@app.get("/ping")
async def ping() -> Dict[str, str]:
    """Ping endpoint for error testing."""
    return {"ping": "pong"}


@app.post("/api/v1/add_user")
async def add_user(
    username: str,
    email: str,
    password: str,
    db_session: Session = Depends(get_db_session),
) -> str:
    """Add a new user to the database."""
    new_user = User(username=username, email=email, password=password)
    db_session.add(new_user)
    db_session.commit()
    return f"Successfully added new user with username: {username} and email: {email}"


@app.get("/api/v1/get_user_info")
async def get_user(
    username: str, db_session: Session = Depends(get_db_session)
) -> User:
    """Get user information by username."""
    user = db_session.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=404, detail=f"User with username: {username} not found."
        )
    return user


@app.post("/api/v1/create_checklist")
async def create_checklist(
    username: str, checklist_title: str, db_session: Session = Depends(get_db_session)
) -> str:
    """Add a new checklist to the database for a user by username."""
    user = db_session.query(User).filter(User.username == username).first()
    checklist = Checklist(title=checklist_title, users=[user])
    db_session.add(checklist)
    db_session.commit()
    return f"Successfully added new checklist with title: {checklist.title} and for user: {user.username}"


@app.get("/api/v1/get_checklists_for_user")
async def get_checklists_for_user(
    username: str, db_session: Session = Depends(get_db_session)
) -> list[Checklist]:
    """Get all checklists for a user by username."""
    user = db_session.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=404, detail=f"User with username: {username} not found."
        )
    return user.checklists


@app.get("/api/v1/add_user_to_checklist")
async def add_user_to_checklist(
    username: str, checklist_id: str, db_session: Session = Depends(get_db_session)
) -> str:
    """Add a user to a checklist by username and checklist id."""
    checklist = db_session.query(Checklist).filter(Checklist.id == checklist_id).first()
    if not checklist:
        raise HTTPException(
            status_code=404, detail=f"Checklist with id: {checklist_id} not found."
        )
    user = db_session.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=404, detail=f"User with username: {username} not found."
        )
    if user in checklist.users:
        raise HTTPException(
            status_code=404,
            detail=f"Username: {username} already in checklist: {checklist.title}.",
        )
    checklist.users.append(user)
    db_session.commit()
    return f"Successfully added user: {user.username} to checklist: {checklist.title}"


@app.get("/api/v1/get_checklist_info")
async def get_checklist_info(
    checklist_id: str, db_session: Session = Depends(get_db_session)
) -> Checklist:
    """Get all users in a checklist by checklist id."""
    checklist = (
        db_session.query(Checklist).filter(Checklist.id == UUID(checklist_id)).first()
    )
    if not checklist:
        raise HTTPException(
            status_code=404, detail=f"Checklist with id: {checklist_id} not found."
        )
    return checklist


@app.get("/api/v1/add_item_to_checklist")
async def add_item_to_checklist(
    checklist_id: str, item_title: str, db_session: Session = Depends(get_db_session)
) -> str:
    """Add an item to a checklist by checklist id."""
    checklist = (
        db_session.query(Checklist).filter(Checklist.id == UUID(checklist_id)).first()
    )
    if not checklist:
        raise HTTPException(
            status_code=404, detail=f"Checklist with id: {checklist_id} not found."
        )
    new_item = Item(title=item_title, checklist_id=checklist.id, checklist=checklist)
    checklist.items.append(new_item)
    db_session.commit()
    return f"Successfully added item: {item_title} to checklist: {checklist.title}"


@app.get("/api/v1/get_items_for_checklist")
async def get_items_for_checklist(
    checklist_id: str, db_session: Session = Depends(get_db_session)
) -> list[Item]:
    """Get all items for a checklist by checklist id."""
    checklist = (
        db_session.query(Checklist).filter(Checklist.id == UUID(checklist_id)).first()
    )
    if not checklist:
        raise HTTPException(
            status_code=404, detail=f"Checklist with id: {checklist_id} not found."
        )
    return checklist.items
