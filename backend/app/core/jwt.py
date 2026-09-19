"""JWT handling per ADR-003/005.

Two audiences (store vs admin) use distinct secrets, distinct cookie names
and distinct refresh families, but share the same claims schema:
sub=user_id, role, iat, exp, aud.
Refresh tokens are opaque random strings stored hashed; access tokens are JWTs.
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Response

from app.core.config import get_settings

# ---------------------------------------------------------------------------
# Audience identifiers (ADR-003)
# ---------------------------------------------------------------------------

AUD_STORE = "store"
AUD_ADMIN = "admin"

# ---------------------------------------------------------------------------
# Cookie names/paths per audience (ADR-003/005), shared by deps and routes.
# Store cookies keep their historical names/paths: the storefront must not break.
# ---------------------------------------------------------------------------

STORE_ACCESS_COOKIE = "access_token"
STORE_REFRESH_COOKIE = "refresh_token"
STORE_REFRESH_PATH = "/auth/refresh"

ADMIN_ACCESS_COOKIE = "admin_access_token"
ADMIN_REFRESH_COOKIE = "admin_refresh_token"
ADMIN_REFRESH_PATH = "/admin/auth/refresh"


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
        "aud": AUD_ADMIN if is_admin else AUD_STORE,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def create_refresh_token_raw() -> str:
    """Generate opaque refresh token value."""
    return secrets.token_urlsafe(48)


def _secret_for(audience: str) -> str:
    settings = get_settings()
    if audience == AUD_ADMIN:
        return settings.jwt_secret_admin
    if audience == AUD_STORE:
        return settings.jwt_secret_store
    raise ValueError(f"Unknown JWT audience: {audience!r}")


def verify_token(token: str, *, audience: str) -> dict:
    """Verify a JWT against ONLY the given audience's secret (ADR-005).

    Enforces signature (single secret, no cross-secret fallback), expiration,
    and that the decoded ``aud`` claim equals the requested audience. A token
    minted for one audience is rejected everywhere else.
    """
    return jwt.decode(
        token,
        _secret_for(audience),
        algorithms=["HS256"],
        audience=audience,
    )


def decode_without_verify(token: str) -> dict | None:
    """Introspection only: read claims without verifying (never authorize with this)."""
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Cookie helpers shared by the store and admin auth surfaces
# ---------------------------------------------------------------------------


def set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    refresh_token: str,
    is_admin: bool = False,
) -> None:
    """Issue the audience's httponly cookie pair (SameSite=Lax per ADR-003).

    Secure=False for local dev/test; in production should be True (HTTPS).
    """
    if is_admin:
        access_name, refresh_name, refresh_path = (
            ADMIN_ACCESS_COOKIE,
            ADMIN_REFRESH_COOKIE,
            ADMIN_REFRESH_PATH,
        )
    else:
        access_name, refresh_name, refresh_path = (
            STORE_ACCESS_COOKIE,
            STORE_REFRESH_COOKIE,
            STORE_REFRESH_PATH,
        )
    settings = get_settings()
    response.set_cookie(
        key=access_name,
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=settings.access_token_expire_minutes * 60,
    )
    response.set_cookie(
        key=refresh_name,
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path=refresh_path,
        max_age=settings.refresh_token_expire_days * 24 * 3600,
    )


def clear_auth_cookies(response: Response, *, is_admin: bool = False) -> None:
    """Clear the audience's cookie pair (paths must match how they were set)."""
    if is_admin:
        response.delete_cookie(key=ADMIN_ACCESS_COOKIE, path="/")
        response.delete_cookie(key=ADMIN_REFRESH_COOKIE, path=ADMIN_REFRESH_PATH)
    else:
        response.delete_cookie(key=STORE_ACCESS_COOKIE, path="/")
        response.delete_cookie(key=STORE_REFRESH_COOKIE, path=STORE_REFRESH_PATH)
