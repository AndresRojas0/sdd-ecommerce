"""Auth dependencies per AUTH-09, AUTH-10, ADR-003/005.

Two isolated audiences:
  - store: Cookie access_token (Path=/) verified with the store secret
  - admin: Cookie admin_access_token (Path=/) verified with the admin secret
Both fall back to Authorization: Bearer <token> for testability.
A token minted for one audience is rejected on the other (ADR-005).
"""
from __future__ import annotations

import uuid

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.jwt import AUD_ADMIN, AUD_STORE, verify_token
from app.db.base import get_db
from app.models.user import User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_token(request: Request, cookie_value: str | None) -> str | None:
    # 1. cookie
    if cookie_value:
        return cookie_value
    # 2. Authorization header
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def _authenticate(request: Request, db: Session, token: str | None, *, audience: str) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    try:
        payload = verify_token(token, audience=audience)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sin sub")
    try:
        uid = uuid.UUID(str(user_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sub inválido")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    # stash payload for role checks without extra DB query if needed
    request.state.jwt_payload = payload
    request.state.jwt_audience = audience
    return user


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    access_token: str | None = Cookie(default=None),
) -> User:
    """Store-audience authentication (Cookie access_token / Bearer)."""
    return _authenticate(request, db, _extract_token(request, access_token), audience=AUD_STORE)


def get_admin_user(
    request: Request,
    db: Session = Depends(get_db),
    admin_access_token: str | None = Cookie(default=None),
) -> User:
    """Admin-audience authentication (Cookie admin_access_token / Bearer)."""
    return _authenticate(request, db, _extract_token(request, admin_access_token), audience=AUD_ADMIN)


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCOUNT_DEACTIVATED", "message": "Cuenta desactivada"},
        )
    if current_user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "MUST_CHANGE_PASSWORD", "message": "Debe cambiar su contraseña"},
        )
    return current_user


def get_admin_active_user(
    current_user: User = Depends(get_admin_user),
) -> User:
    """Admin-audience mirror of get_current_active_user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCOUNT_DEACTIVATED", "message": "Cuenta desactivada"},
        )
    if current_user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "MUST_CHANGE_PASSWORD", "message": "Debe cambiar su contraseña"},
        )
    return current_user


def require_role(*roles: str):
    """Factory returning a store-audience dependency that enforces role."""

    def _check(user: User = Depends(get_current_active_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para este recurso")
        return user

    return _check


def require_admin_role(*roles: str):
    """Factory returning an admin-audience dependency that enforces role."""

    def _check(user: User = Depends(get_admin_active_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para este recurso")
        return user

    return _check


# Optional user (for visits: authenticated or anonymous) — store audience only
def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
    access_token: str | None = Cookie(default=None),
) -> User | None:
    token = _extract_token(request, access_token)
    if not token:
        return None
    try:
        payload = verify_token(token, audience=AUD_STORE)
        uid = uuid.UUID(str(payload.get("sub")))
        user = db.get(User, uid)
        if user and user.is_active and not user.must_change_password:
            return user
    except Exception:
        pass
    return None
