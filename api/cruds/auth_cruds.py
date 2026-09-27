from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models.models import AppUser, UserSession
from security import hash_password, hash_session_id, verify_password


def get_user_by_app_id(db_session: Session, app_id: str) -> AppUser | None:
    return db_session.scalar(select(AppUser).where(AppUser.app_id == app_id))


def get_user_by_email(db_session: Session, email: str) -> AppUser | None:
    return db_session.scalar(select(AppUser).where(AppUser.email == email))


def get_user_by_identifier(db_session: Session, identifier: str) -> AppUser | None:
    return db_session.scalar(
        select(AppUser).where(
            (AppUser.app_id == identifier) | (AppUser.email == identifier)
        )
    )


def create_user(
    db_session: Session,
    app_id: str,
    password: str,
    name: str | None = None,
    email: str | None = None,
) -> AppUser:
    user = AppUser(
        app_id=app_id,
        name=name,
        email=email,
        hashed_password=hash_password(password),
    )
    db_session.add(user)
    db_session.flush()
    return user


def authenticate_user(
    db_session: Session, identifier: str, password: str
) -> AppUser | None:
    user = get_user_by_identifier(db_session, identifier)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


def create_user_session(
    db_session: Session, user: AppUser, raw_session_id: str, expires_at: datetime
) -> UserSession:
    user_session = UserSession(
        session_id_hash=hash_session_id(raw_session_id),
        user_id=user.id,
        expires_at=expires_at,
    )
    db_session.add(user_session)
    db_session.flush()
    return user_session


def get_valid_session(db_session: Session, raw_session_id: str) -> UserSession | None:
    user_session = db_session.scalar(
        select(UserSession).where(
            UserSession.session_id_hash == hash_session_id(raw_session_id)
        )
    )
    if user_session is None:
        return None
    expires_at = user_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        db_session.delete(user_session)
        db_session.commit()
        return None
    return user_session


def delete_session_by_raw_id(db_session: Session, raw_session_id: str) -> None:
    db_session.execute(
        delete(UserSession).where(
            UserSession.session_id_hash == hash_session_id(raw_session_id)
        )
    )
