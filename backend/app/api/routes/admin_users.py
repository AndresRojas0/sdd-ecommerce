"""Admin user management — UC-AD01..05, AUTH-12, RN-17, RF-32; lifecycle A-USR-07..09."""
from __future__ import annotations

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.api.deps import require_admin_role
from app.core.audit import registrar_auditoria
from app.core.security import PasswordPolicyError, hash_password, validate_policy
from app.db.base import get_db
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user import (
    AdminUserCreateResponse,
    AdminUserProfileUpdate,
    AdminUserResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    RoleChangeRequest,
    UserCreateRequest,
)
from app.api.routes.orders import _pedido_to_response

router = APIRouter(prefix="/admin/users", tags=["admin-users"])

_AVISO_TEMP_PASSWORD = "Mostrar una sola vez"


def _generate_temp_password() -> str:
    """Temp password always policy-compliant (AUTH-04): `Tp-` adds uppercase +
    lowercase, `!7A` guarantees digit + special char regardless of the hex body."""
    return f"Tp-{secrets.token_hex(4)}!7A"


def _resolve_temp_password(provided: str | None) -> str:
    """Validates the provided temp password (AUTH-04) or generates one."""
    temp = provided or _generate_temp_password()
    try:
        validate_policy(temp)
    except PasswordPolicyError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return temp


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


# ---------------------------------------------------------------------------
# A-USR-07 — POST /admin/users (alta desde el panel, solo `administrador`)
# ---------------------------------------------------------------------------


@router.post("", status_code=201, response_model=AdminUserCreateResponse)
def create_user(
    body: UserCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_role("administrador")),
):
    """Crea comprador/vendedor con contraseña temporal y `must_change_password=True`.

    El rol `administrador` NO es asignable desde el panel (422): el bootstrap
    por env (BOOT-01/02, ADR-006) es el único camino. El `temp_password`
    viaja SOLO en esta respuesta y nunca se registra en auditoría.
    """
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El email ya está registrado (RN-14)",
        )
    temp = _resolve_temp_password(body.temp_password)
    user = User(
        email=body.email,
        display_name=body.display_name,
        role=body.role,
        password_hash=hash_password(temp),
        is_active=True,
        must_change_password=True,
    )
    db.add(user)
    db.flush()
    registrar_auditoria(
        db,
        request,
        current_user,
        accion="usuario.crear",
        entidad="usuario",
        entidad_id=user.id,
        despues={"email": user.email, "role": user.role},
    )
    db.commit()
    db.refresh(user)
    return AdminUserCreateResponse(
        user=AdminUserResponse.model_validate(user),
        temp_password=temp,
        aviso=_AVISO_TEMP_PASSWORD,
    )


# ---------------------------------------------------------------------------
# A-USR-08 — POST /admin/users/{user_id}/password-reset (solo `administrador`)
# ---------------------------------------------------------------------------


@router.post("/{user_id}/password-reset", response_model=PasswordResetResponse)
def reset_user_password(
    user_id: uuid.UUID,
    body: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_role("administrador")),
):
    """Restablece la contraseña a una temporal forzando el cambio en el próximo login.

    Opera sobre cualquier usuario (incluidos otros administradores) y revoca
    TODAS sus filas de refresh token (ambas audiencias), igual que
    `change-password-force` (A-AUTH-05). Nunca revela el hash: la contraseña
    temporal viaja una sola vez en esta respuesta.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    temp = _resolve_temp_password(body.temp_password)
    user.password_hash = hash_password(temp)
    user.must_change_password = True
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user.id).values(revoked=True))
    registrar_auditoria(
        db,
        request,
        current_user,
        accion="usuario.reset_password",
        entidad="usuario",
        entidad_id=user.id,
    )
    db.commit()
    return PasswordResetResponse(temp_password=temp, aviso=_AVISO_TEMP_PASSWORD)


# ---------------------------------------------------------------------------
# A-USR-09 — PATCH /admin/users/{user_id}/role (solo `administrador`)
# ---------------------------------------------------------------------------


@router.patch("/{user_id}/role", response_model=AdminUserResponse)
def change_user_role(
    user_id: uuid.UUID,
    body: RoleChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_role("administrador")),
):
    """Cambia el rol de un usuario entre `comprador` y `vendedor`.

    Guard: un administrador no puede cambiar su PROPIO rol (evita
    auto-bloqueo si queda sin administradores activos). No hay promoción
    a `administrador` desde el panel (bootstrap por env, ADR-006).
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No puede cambiar su propio rol (evitar auto-bloqueo)",
        )
    rol_anterior = user.role
    user.role = body.role
    registrar_auditoria(
        db,
        request,
        current_user,
        accion="usuario.cambiar_rol",
        entidad="usuario",
        entidad_id=user.id,
        antes={"role": rol_anterior},
        despues={"role": user.role},
    )
    db.commit()
    db.refresh(user)
    return user
