"""Configuration for the project."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from sqlmodel import Session, SQLModel, create_engine


class Settings:
    """Settings for the project."""

    PROJECT_NAME: str = "WeBucket"
    PROJECT_VERSION: str = "1.0.0"


app = FastAPI(title=Settings.PROJECT_NAME, version=Settings.PROJECT_VERSION)

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


config = {"database": {"url": "sqlite:///database_service/db.sqlite"}}

engine = create_engine(
    config["database"]["url"], echo=True, connect_args={"check_same_thread": False}
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db_session() -> Session:
    """Make a new database session for each request."""
    with Session(engine) as session:
        yield session


def init_db() -> None:
    """Create the database tables on startup."""
    print("Starting up...")
    SQLModel.metadata.create_all(engine)
    print(f"Project name: {Settings.PROJECT_NAME}")
    print(f"Project version: {Settings.PROJECT_VERSION}")
    print(f"Database URL: {config['database']['url']}")
