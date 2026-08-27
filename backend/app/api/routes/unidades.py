"""Unidades medida — RN-23 extensible."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.base import get_db
from app.models.unidad_medida import UnidadMedida
from app.schemas.unidad import UnidadCreate, UnidadResponse

router = APIRouter(prefix="/unidades-medida", tags=["unidades-medida"])


@router.get("", response_model=list[UnidadResponse])
def list_unidades(db: Session = Depends(get_db)):
    return db.scalars(select(UnidadMedida).order_by(UnidadMedida.nombre)).all()


@router.post("", response_model=UnidadResponse, status_code=status.HTTP_201_CREATED)
def create_unidad(
    body: UnidadCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador")),
):
    unidad = UnidadMedida(nombre=body.nombre, simbolo=body.simbolo)
    db.add(unidad)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unidad ya existe")
    db.refresh(unidad)
    return unidad


@router.delete("/{unidad_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unidad(
    unidad_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador")),
):
    unidad = db.get(UnidadMedida, unidad_id)
    if not unidad:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidad no encontrada")
    try:
        db.delete(unidad)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unidad en uso por productos")
    return None
