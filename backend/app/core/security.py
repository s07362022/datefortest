from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the hashed password."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: int, is_admin: bool = False) -> str:
    """Create a signed JWT access token.

    Payload includes user_id, is_admin, issued_at, and expires_at
    as required by the SPEC.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "user_id": user_id,
        "is_admin": is_admin,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT token.

    Raises JWTError on invalid or expired tokens.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
