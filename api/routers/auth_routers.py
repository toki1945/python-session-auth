import os
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from cruds import auth_cruds
from database import get_db
from dependencies import get_current_user
from models.models import AppUser
from schemas.user_schemas import UserCreate, UserLogin, UserRead
from security import generate_session_id

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_MAX_AGE = 60 * 60 * 24 * 7


def cookie_secure() -> bool:
    return os.getenv("COOKIE_SECURE", "true").lower() in {"1", "true", "yes"}


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> AppUser:
    if auth_cruds.get_user_by_app_id(db, payload.app_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="app_id already taken"
        )
    if payload.email is not None and auth_cruds.get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="email already registered"
        )

    try:
        user = auth_cruds.create_user(
            db,
            app_id=payload.app_id,
            password=payload.password,
            name=payload.name,
            email=payload.email,
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="app_id or email already taken",
        )
    db.refresh(user)
    return user


@router.post("/login", response_model=UserRead)
def login(
    payload: UserLogin, response: Response, db: Session = Depends(get_db)
) -> AppUser:
    user = auth_cruds.authenticate_user(db, payload.identifier, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    raw_session_id = generate_session_id()
    expires_at = datetime.now(UTC) + timedelta(seconds=SESSION_MAX_AGE)
    auth_cruds.create_user_session(db, user, raw_session_id, expires_at)
    db.commit()

    response.set_cookie(
        key="session_id",
        value=raw_session_id,
        httponly=True,
        secure=cookie_secure(),
        samesite="lax",
        max_age=SESSION_MAX_AGE,
        path="/",
    )
    return user


@router.get("/me", response_model=UserRead)
def me(user: AppUser = Depends(get_current_user)) -> AppUser:
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    session_id: Annotated[str | None, Cookie()] = None,
    db: Session = Depends(get_db),
) -> None:
    if session_id:
        auth_cruds.delete_session_by_raw_id(db, session_id)
        db.commit()
    response.delete_cookie(
        "session_id",
        path="/",
        secure=cookie_secure(),
        httponly=True,
        samesite="lax",
    )
