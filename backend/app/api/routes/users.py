"""User profile endpoints — UC-C06/07/09/10, RF-28, RN-17/19."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_user
from app.db.base import get_db
from app.models.pedido import Pedido
from app.models.user import User
from app.schemas.auth import ReactivateRequest, UserResponse
from app.schemas.user import UpdateAvatarRequest, UpdateMeRequest
from app.core.security import verify_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_me(
    body: UpdateMeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    current_user.display_name = body.display_name
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/me/avatar", response_model=UserResponse)
def update_avatar(
    body: UpdateAvatarRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    current_user.avatar = body.avatar
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/deactivate", response_model=UserResponse)
def deactivate_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    delete_pending: bool = Query(default=False, description="Eliminar pedidos pendientes"),
):
    current_user.is_active = False
    if delete_pending:
        # RN-19: delete only pending orders, never purchase-order linked
        db.execute(
            delete(Pedido).where(Pedido.user_id == current_user.id, Pedido.estado == "pendiente")
        )
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/reactivate", response_model=UserResponse)
def reactivate_me(
    body: ReactivateRequest,
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(User.email == body.email))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    if user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La cuenta ya está activa")
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


# Variant that uses authenticated user (if they kept token before deactivation)
@router.post("/me/reactivate-auth", response_model=UserResponse)
def reactivate_auth(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya activa")
    current_user.is_active = True
    db.commit()
    db.refresh(current_user)
    return current_user
