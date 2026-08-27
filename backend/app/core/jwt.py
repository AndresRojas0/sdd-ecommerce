"""JWT handling per ADR-003.

Two audiences (store vs admin) use distinct secrets but share the same
claims schema: sub=user_id, role, iat, exp.
Refresh tokens are opaque random strings stored hashed; access tokens are JWTs.
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import get_settings


def hash_token(raw: str) -> str:
    """SHA-256 hash for refresh token storage (data-model.md §16)."""
    return hashlib.sha256(raw.encode()).hexdigest()


def create_access_token(user_id: uuid.UUID, role: str, *, is_admin: bool = False) -> str:
    settings = get_settings()
    secret = settings.jwt_secret_admin if is_admin else settings.jwt_secret_store
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "aud": "admin" if is_admin else "store",
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def create_refresh_token_raw() -> str:
    """Generate opaque refresh token value."""
    return secrets.token_urlsafe(48)


def verify_token(token: str) -> dict:
    """Verify JWT trying store secret then admin secret.

    Returns decoded payload or raises jwt exceptions.
    For MVP we accept either audience; role claim authorizes.
    """
    settings = get_settings()
    last_exc = None
    for secret in (settings.jwt_secret_store, settings.jwt_secret_admin):
        try:
            # verify exp/iat; allow both audiences
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            return payload
        except jwt.PyJWTError as exc:
            last_exc = exc
            continue
    raise last_exc  # type: ignore[misc]


def decode_without_verify(token: str) -> dict | None:
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except Exception:
        return None
