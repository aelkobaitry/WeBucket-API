"""Main FastAPI module file with endpoints."""

from pathlib import Path
from typing import Dict

from config import Settings
from fastapi import Depends, FastAPI, HTTPException
from schema import Checklist, User
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


@app.get("/api/v1/user_info")
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


@app.post("/api/v1/add_checklist")
async def add_checklist(
    username: str, checklist_title: str, db_session: Session = Depends(get_db_session)
) -> str:
    """Add a new checklist to the database for a user by username."""
    user = db_session.query(User).filter(User.username == username).first()
    checklist = Checklist(title=checklist_title, users=[user])
    db_session.add(checklist)
    db_session.commit()
    return f"Successfully added new checklist with title: {checklist.title} and for user: {user.username}"


@app.get("/api/v1/user_checklists")
async def get_user_checklists(
    username: str, db_session: Session = Depends(get_db_session)
) -> list[Checklist]:
    """Get all checklists for a user by username."""
    user = db_session.query(User).filter(User.username == username).first()
    return user.checklists
