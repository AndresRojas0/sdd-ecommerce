"""Admin user management — UC-AD01..05, AUTH-12, RN-17, RF-32."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin_role
from app.core.audit import registrar_auditoria
from app.db.base import get_db
from app.models.user import User
from app.schemas.user import AdminUserResponse, AdminUserProfileUpdate
from app.api.routes.orders import _pedido_to_response

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("", response_model=dict)
def list_users(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_role("administrador", "vendedor")),
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
    current_user=Depends(require_admin_role("administrador", "vendedor")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user


@router.patch("/{user_id}", response_model=AdminUserResponse)
def update_user_profile(
    user_id: uuid.UUID,
    body: AdminUserProfileUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_role("administrador", "vendedor")),
):
    """A-USR-03: edición acotada de perfil — NO rol, NO contraseña (RF-32).

    Campos permitidos: display_name, avatar. Cualquier otro campo
    (incluidos role/password) se rechaza con 422 (extra=forbid).
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    antes: dict = {}
    despues: dict = {}
    if body.display_name is not None:
        nuevo = body.display_name.strip()
        if not nuevo:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="display_name no puede quedar vacío")
        antes["display_name"] = user.display_name
        user.display_name = nuevo
        despues["display_name"] = user.display_name
    if "avatar" in body.model_fields_set:
        antes["avatar"] = user.avatar
        user.avatar = body.avatar
        despues["avatar"] = user.avatar
    registrar_auditoria(
        db,
        request,
        current_user,
        accion="usuario.editar_perfil",
        entidad="usuario",
        entidad_id=user.id,
        antes=antes or None,
        despues=despues or None,
    )
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}/metrics", response_model=dict)
def get_user_metrics(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_role("administrador", "vendedor")),
):
    """A-USR-05: métricas del usuario — cantidad de pedidos, gasto total, último pedido (UC-AD24)."""
    from app.models.pedido import Pedido

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    orders_count = db.scalar(select(func.count()).select_from(Pedido).where(Pedido.user_id == user.id)) or 0
    total_spent = db.scalar(select(func.coalesce(func.sum(Pedido.total), 0)).where(Pedido.user_id == user.id)) or 0
    last_order_at = db.scalar(select(func.max(Pedido.created_at)).where(Pedido.user_id == user.id))
    return {
        "user_id": str(user.id),
        "orders_count": orders_count,
        "total_spent": str(total_spent),
        "last_order_at": last_order_at.isoformat() if last_order_at else None,
    }


@router.get("/{user_id}/orders", response_model=dict)
def list_user_orders(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_role("administrador", "vendedor")),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """A-USR-06: todos los pedidos del usuario (paginado, reutiliza el serializador admin)."""
    from app.models.pedido import Pedido

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    total = db.scalar(select(func.count()).select_from(Pedido).where(Pedido.user_id == user.id)) or 0
    pedidos = db.scalars(
        select(Pedido).where(Pedido.user_id == user.id).order_by(Pedido.created_at.desc()).limit(limit).offset(offset)
    ).all()
    items = [_pedido_to_response(db, p).model_dump() for p in pedidos]
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@router.patch("/{user_id}/activate", response_model=AdminUserResponse)
def activate_user(
    user_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_role("administrador")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    estado_anterior = user.is_active
    user.is_active = True
    registrar_auditoria(
        db,
        request,
        current_user,
        accion="usuario.activar",
        entidad="usuario",
        entidad_id=user.id,
        antes={"is_active": estado_anterior},
        despues={"is_active": user.is_active},
    )
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/deactivate", response_model=AdminUserResponse)
def deactivate_user(
    user_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_role("administrador")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    estado_anterior = user.is_active
    user.is_active = False
    registrar_auditoria(
        db,
        request,
        current_user,
        accion="usuario.desactivar",
        entidad="usuario",
        entidad_id=user.id,
        antes={"is_active": estado_anterior},
        despues={"is_active": user.is_active},
    )
    db.commit()
    db.refresh(user)
    return user
