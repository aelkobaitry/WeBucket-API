"""Authentication module for user login and token generation."""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel
from sqlmodel import Session

from src.config import app, get_db_session, pwd_context
from src.schema import User

# openssl rand -hex 32
SECRET_KEY = "45781253ad135938709c470a6b1f19a899965d6861fa05b5f15018c27780f310"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 45

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    """Basic token authentication model."""

    access_token: str
    token_type: str


def authenticate_user(username: str, password: str, db_session: Session):
    """Authenticate a user by username and password against the db."""
    user = db_session.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create an access token with the given data and expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_active_user(
    token: str = Depends(oauth2_scheme), db_session: Session = Depends(get_db_session)
):
    """Get the current active user from the token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data_username = username
    except InvalidTokenError:
        raise credentials_exception from None
    user = db_session.query(User).filter(User.username == token_data_username).first()
    if user is None:
        raise credentials_exception
    return user


@app.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_session: Session = Depends(get_db_session),
) -> Token:
    """Login endpoint for generating an access token."""
    user = authenticate_user(form_data.username, form_data.password, db_session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
