"""Auth endpoints — UC-C01..C10, RF-01, RN-14/15, ADR-003.

Endpoints:
  POST /auth/register
  POST /auth/login
  POST /auth/logout
  POST /auth/refresh
  POST /auth/change-password
  GET  /auth/me
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_user
from app.core.config import get_settings
from app.core.jwt import create_access_token, create_refresh_token_raw, hash_token
from app.core.security import PasswordPolicyError, hash_password, validate_policy, verify_password
from app.db.base import get_db
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    ReactivateRequest,
    RegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    # Secure=False for local dev/test; in production should be True (HTTPS).
    # SameSite=Lax per ADR-003.
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=15 * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/auth/refresh",
        max_age=30 * 24 * 3600,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/auth/refresh")


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    # Policy already validated by Pydantic, but double-check
    try:
        validate_policy(body.password)
    except PasswordPolicyError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    existing = db.scalar(select(User).where(User.email == body.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya registrado")
    user = User(
        email=body.email,
        display_name=body.display_name,
        avatar=body.avatar,
        password_hash=hash_password(body.password),
        role="comprador",
        is_active=True,
        must_change_password=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


@router.post("/login")
def login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    reactivate: bool = Query(default=False, description="Reactivar cuenta dada de baja"),
):
    user: User | None = db.scalar(select(User).where(User.email == body.email))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    # Deactivated account
    if not user.is_active:
        if reactivate:
            user.is_active = True
            db.commit()
            db.refresh(user)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "ACCOUNT_DEACTIVATED", "message": "Cuenta desactivada. Use reactivate=true para reactivar."},
            )

    # Must change password (BOOT-03)
    if user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "MUST_CHANGE_PASSWORD", "message": "Debe cambiar su contraseña antes de continuar."},
        )

    # Issue tokens
    access_token = create_access_token(user.id, user.role)
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
    )
    db.add(rt)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    _set_auth_cookies(response, access_token, raw_refresh)
    return {"user": UserResponse.model_validate(user), "message": "Login exitoso"}


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------


@router.post("/logout")
def logout(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
    current_user: User = Depends(get_current_user),
):
    # Revoke all families for user or specific family if cookie present
    if refresh_token:
        token_hash = hash_token(refresh_token)
        rt = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        if rt:
            # Revoke entire family
            db.execute(
                update(RefreshToken)
                .where(RefreshToken.family_id == rt.family_id)
                .values(revoked=True)
            )
            db.commit()
        else:
            # Fallback: revoke all for user
            db.execute(
                update(RefreshToken)
                .where(RefreshToken.user_id == current_user.id)
                .values(revoked=True)
            )
            db.commit()
    else:
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == current_user.id)
            .values(revoked=True)
        )
        db.commit()
    _clear_auth_cookies(response)
    return {"message": "Logout exitoso"}


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------


@router.post("/refresh")
def refresh(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token faltante")
    token_hash = hash_token(refresh_token)
    rt = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))

    if not rt:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")

    # If token already revoked → reuse detection → revoke entire family
    if rt.revoked:
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == rt.family_id)
            .values(revoked=True)
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Reuse detectado: familia revocada")

    # Expiry check
    now = datetime.now(timezone.utc)
    # Ensure expires_at is timezone-aware for comparison
    expires = rt.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expirado")

    # Also check family compromised already? If any revoked in family beyond this one?
    # Already handled via reuse detection.

    # Rotate: revoke old, issue new with same family
    rt.revoked = True
    # Load user
    user = db.get(User, rt.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no válido")

    new_raw = create_refresh_token_raw()
    settings = get_settings()
    new_expires = now + timedelta(days=settings.refresh_token_expire_days)
    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_raw),
        family_id=rt.family_id,
        expires_at=new_expires,
        revoked=False,
    )
    db.add(new_rt)
    db.commit()

    new_access = create_access_token(user.id, user.role)
    _set_auth_cookies(response, new_access, new_raw)
    return {"message": "Tokens renovados"}


# ---------------------------------------------------------------------------
# POST /auth/change-password
# ---------------------------------------------------------------------------


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    db.execute(
        update(RefreshToken).where(RefreshToken.user_id == current_user.id).values(revoked=True)
    )
    db.commit()
    _clear_auth_cookies(response)
    return {"message": "Contraseña cambiada. Inicie sesión nuevamente."}


# Additional endpoint that allows must_change_password users to change password
@router.post("/change-password-force")
def change_password_force(
    body: ChangePasswordRequest,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    db.execute(update(RefreshToken).where(RefreshToken.user_id == current_user.id).values(revoked=True))
    db.commit()
    _clear_auth_cookies(response)
    return {"message": "Contraseña cambiada. Inicie sesión nuevamente."}


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_active_user)):
    return current_user


# ---------------------------------------------------------------------------
# POST /users/me/reactivate alternative via auth
# ---------------------------------------------------------------------------


@router.post("/reactivate", status_code=status.HTTP_200_OK)
def reactivate_via_auth(body: ReactivateRequest, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    if user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La cuenta ya está activa")
    user.is_active = True
    db.commit()
    db.refresh(user)
    # Issue tokens after reactivation
    access_token = create_access_token(user.id, user.role)
    raw_refresh = create_refresh_token_raw()
    family_id = uuid.uuid4()
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_refresh),
        family_id=family_id,
        expires_at=expires_at,
    )
    db.add(rt)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    _set_auth_cookies(response, access_token, raw_refresh)
    return {"user": UserResponse.model_validate(user), "message": "Cuenta reactivada"}
