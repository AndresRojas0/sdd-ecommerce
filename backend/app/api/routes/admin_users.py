"""Admin user management — UC-AD01..04, AUTH-12, RN-17."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.base import get_db
from app.models.user import User
from app.schemas.user import AdminUserResponse

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("", response_model=dict)
def list_users(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador", "vendedor")),
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None, description="Filtra por email o display_name (UC-V03)"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    filters = []
    if role:
        filters.append(User.role == role)
    if is_active is not None:
        filters.append(User.is_active == is_active)
    if search:
        from sqlalchemy import or_

        like = f"%{search}%"
        filters.append(or_(User.email.ilike(like), User.display_name.ilike(like)))
    base = select(User)
    count_base = select(func.count()).select_from(User)
    if filters:
        from sqlalchemy import and_

        base = base.where(and_(*filters))
        count_base = count_base.where(and_(*filters))
    total = db.scalar(count_base) or 0
    users = db.scalars(base.order_by(User.created_at.desc()).limit(limit).offset(offset)).all()
    items = [AdminUserResponse.model_validate(u).model_dump() for u in users]
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@router.get("/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador", "vendedor")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user


@router.patch("/{user_id}/activate", response_model=AdminUserResponse)
def activate_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/deactivate", response_model=AdminUserResponse)
def deactivate_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user



