import hashlib
import secrets

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_session_id() -> str:
    """Generate the opaque value sent only in the session cookie."""
    return secrets.token_urlsafe(32)


def hash_session_id(session_id: str) -> str:
    """Hash a session id before it is persisted."""
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()
