"""Cookie-session authentication dependencies."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from database import get_db
from models.models import AppUser, UserSession
from security import hash_session_id


def get_current_user(
    session_id: Annotated[str | None, Cookie()] = None,
    db_session: Session = Depends(get_db),
) -> AppUser:
    if not session_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    now = datetime.now(UTC)
    user = db_session.scalar(
        select(AppUser)
        .join(UserSession, UserSession.user_id == AppUser.id)
        .where(
            UserSession.session_id_hash == hash_session_id(session_id),
            UserSession.expires_at > now,
        )
    )
    if user is None:
        db_session.execute(delete(UserSession).where(UserSession.expires_at <= now))
        db_session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )
    return user
