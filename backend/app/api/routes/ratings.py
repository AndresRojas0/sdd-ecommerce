"""Ratings — RN-21 promedio fraccional, RN-33 elegibilidad, UC-B10."""
from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.base import get_db
from app.models.calificacion import Calificacion
from app.models.pedido import Pedido
from app.models.pedido_item import PedidoItem
from app.models.producto import Producto
from app.models.user import User
from app.schemas.calificacion import CalificacionCreate, CalificacionResponse, CalificacionUpdate

router = APIRouter(prefix="/products", tags=["ratings"])


def _recalc_producto(db: Session, product_id: uuid.UUID) -> None:
    prod = db.get(Producto, product_id)
    if not prod:
        return
    avg, cnt = db.execute(
        select(func.avg(Calificacion.estrellas), func.count(Calificacion.id)).where(
            Calificacion.product_id == product_id
        )
    ).one()
    prod.calificacion_promedio = Decimal(str(round(float(avg or 0), 2)))
    prod.calificacion_cantidad = int(cnt or 0)


def _check_eligibility(db: Session, user_id: uuid.UUID, product_id: uuid.UUID) -> bool:
    # EXISTS pedido aceptado with item product_id for user
    exists = db.scalar(
        select(Pedido.id)
        .join(PedidoItem, PedidoItem.pedido_id == Pedido.id)
        .where(
            Pedido.user_id == user_id,
            Pedido.estado == "aceptado",
            PedidoItem.product_id == product_id,
        )
        .limit(1)
    )
    return exists is not None


@router.post("/{product_id}/ratings", response_model=CalificacionResponse, status_code=status.HTTP_201_CREATED)
def create_rating(
    product_id: uuid.UUID,
    body: CalificacionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    prod = db.get(Producto, product_id)
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    if prod.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no disponible")

    if not _check_eligibility(db, current_user.id, product_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puede calificar quien tenga un pedido aceptado que incluya el producto (RN-33)",
        )

    existing = db.scalar(
        select(Calificacion).where(Calificacion.user_id == current_user.id, Calificacion.product_id == product_id)
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya calificó este producto. Use PUT para editar.")

    cal = Calificacion(user_id=current_user.id, product_id=product_id, estrellas=body.estrellas)
    db.add(cal)
    db.flush()
    _recalc_producto(db, product_id)
    db.commit()
    db.refresh(cal)
    return cal


@router.put("/{product_id}/ratings", response_model=CalificacionResponse)
def update_rating(
    product_id: uuid.UUID,
    body: CalificacionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    cal = db.scalar(
        select(Calificacion).where(Calificacion.user_id == current_user.id, Calificacion.product_id == product_id)
    )
    if not cal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calificación no encontrada")
    cal.estrellas = body.estrellas
    db.flush()
    _recalc_producto(db, product_id)
    db.commit()
    db.refresh(cal)
    return cal


@router.get("/{product_id}/ratings", response_model=list[CalificacionResponse])
def list_ratings(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    prod = db.get(Producto, product_id)
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    ratings = db.scalars(select(Calificacion).where(Calificacion.product_id == product_id).order_by(Calificacion.created_at.desc())).all()
    return ratings


@router.delete("/{product_id}/ratings", status_code=status.HTTP_204_NO_CONTENT)
def delete_rating(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    cal = db.scalar(
        select(Calificacion).where(Calificacion.user_id == current_user.id, Calificacion.product_id == product_id)
    )
    if not cal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calificación no encontrada")
    db.delete(cal)
    db.flush()
    _recalc_producto(db, product_id)
    db.commit()
    return None
