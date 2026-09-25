"""Admin auth surface — ADR-003/005.

Separate audience with its own secret, cookies and refresh families:
  POST /admin/auth/login
  POST /admin/auth/refresh
  POST /admin/auth/logout
  GET  /admin/auth/me
  POST /admin/auth/change-password-force

Cookies: admin_access_token (Path=/) + admin_refresh_token
(Path=/admin/auth/refresh) — see core.jwt. Tokens are verified exclusively
against the admin audience; store tokens are rejected here and vice versa.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user
from app.api.routes.auth import revoke_logout, rotate_refresh
from app.core.config import get_settings
from app.core.jwt import (
    AUD_ADMIN,
    clear_auth_cookies,
    create_access_token,
    create_refresh_token_raw,
    hash_token,
    set_auth_cookies,
)
from app.core.security import PasswordPolicyError, hash_password, validate_policy, verify_password
from app.db.base import get_db
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, UserResponse

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])

_ADMIN_ROLES = ("administrador", "vendedor")


# ---------------------------------------------------------------------------
# POST /admin/auth/login
# ---------------------------------------------------------------------------


@router.post("/login")
def admin_login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user: User | None = db.scalar(select(User).where(User.email == body.email))
    if not user or not verify_password(body.password, user.password_hash):
        # Same explicit-message policy as the store surface: no email-existence leak.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    # Deactivated accounts cannot self-reactivate on the admin surface.
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCOUNT_DEACTIVATED", "message": "Cuenta desactivada"},
        )

    # Role gate (not existence): the credentials are valid but this is not staff.
    if user.role not in _ADMIN_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para este recurso")

    # Issue admin-audience tokens BEFORE the must_change check: the 403 below
    # carries the admin session so the client can reach
    # /admin/auth/change-password-force (BOOT-03 first-login flow).
    access_token = create_access_token(user.id, user.role, is_admin=True)
    raw_refresh = create_refresh_token_raw()
    family_id = uuid.uuid4()
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_refresh),
        family_id=family_id,
        expires_at=expires_at,
        revoked=False,
        aud=AUD_ADMIN,
    )
    db.add(rt)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    set_auth_cookies(response, access_token=access_token, refresh_token=raw_refresh, is_admin=True)

    # Must change password (BOOT-03): same 403 contract, but WITH a session.
    # Returned (not raised) so the cookies set above are not discarded by the
    # exception handler.
    if user.must_change_password:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {
            "detail": {
                "code": "MUST_CHANGE_PASSWORD",
                "message": "Debe cambiar su contraseña antes de continuar.",
            }
        }

    return {"user": UserResponse.model_validate(user), "message": "Login exitoso"}


# ---------------------------------------------------------------------------
# POST /admin/auth/refresh
# ---------------------------------------------------------------------------


@router.post("/refresh")
def admin_refresh(
    response: Response,
    db: Session = Depends(get_db),
    admin_refresh_token: str | None = Cookie(default=None),
):
    rotate_refresh(response, db, admin_refresh_token, audience=AUD_ADMIN, is_admin=True)
    return {"message": "Tokens renovados"}


# ---------------------------------------------------------------------------
# POST /admin/auth/logout
# ---------------------------------------------------------------------------


@router.post("/logout")
def admin_logout(
    response: Response,
    db: Session = Depends(get_db),
    admin_refresh_token: str | None = Cookie(default=None),
    current_user: User = Depends(get_admin_user),
):
    # Revoke refresh rows scoped to the admin audience (ADR-005)
    revoke_logout(db, current_user, admin_refresh_token, audience=AUD_ADMIN)
    clear_auth_cookies(response, is_admin=True)
    return {"message": "Logout exitoso"}


# ---------------------------------------------------------------------------
# GET /admin/auth/me
# ---------------------------------------------------------------------------


@router.get("/me", response_model=UserResponse)
def admin_me(current_user: User = Depends(get_admin_user)):
    return current_user


# ---------------------------------------------------------------------------
# POST /admin/auth/change-password-force
# ---------------------------------------------------------------------------


@router.post("/change-password-force")
def admin_change_password_force(
    body: ChangePasswordRequest,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta desactivada")
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Contraseña actual incorrecta")
    try:
        validate_policy(body.new_password)
    except PasswordPolicyError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    current_user.password_hash = hash_password(body.new_password)
    current_user.must_change_password = False
    # Revoke ALL the user's refresh rows across both audiences.
    db.execute(update(RefreshToken).where(RefreshToken.user_id == current_user.id).values(revoked=True))
    db.commit()
    clear_auth_cookies(response, is_admin=True)
    return {"message": "Contraseña cambiada. Inicie sesión nuevamente."}
