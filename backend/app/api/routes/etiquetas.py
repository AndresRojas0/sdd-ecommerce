"""Etiquetas endpoints — RN-02, RN-03 autocomplete."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_role
from app.db.base import get_db
from app.models.etiqueta import Etiqueta
from app.schemas.etiqueta import EtiquetaCreate, EtiquetaResponse

router = APIRouter(prefix="/etiquetas", tags=["etiquetas"])


@router.get("", response_model=list[EtiquetaResponse])
def list_etiquetas(db: Session = Depends(get_db), q: str | None = Query(default=None)):
    stmt = select(Etiqueta).order_by(Etiqueta.nombre)
    if q:
        # Simple ILIKE via ilike for portability; pg_trgm will accelerate
        stmt = select(Etiqueta).where(Etiqueta.nombre.ilike(f"%{q}%")).order_by(Etiqueta.nombre)
    return db.scalars(stmt).all()


@router.get("/autocomplete", response_model=list[EtiquetaResponse])
def autocomplete(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    # RN-03: substring search, limit 10
    stmt = select(Etiqueta).where(Etiqueta.nombre.ilike(f"%{q}%")).order_by(Etiqueta.nombre).limit(10)
    return db.scalars(stmt).all()


@router.post("", response_model=EtiquetaResponse, status_code=status.HTTP_201_CREATED)
def create_etiqueta(
    body: EtiquetaCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("vendedor", "administrador")),
):
    # Create if not exists — but return 409 if duplicate slug/nombre? Spec says create if not exists
    existing = db.scalar(select(Etiqueta).where((Etiqueta.nombre == body.nombre) | (Etiqueta.slug == body.slug)))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Etiqueta ya existe")
    tag = Etiqueta(nombre=body.nombre, slug=body.slug.lower())
    db.add(tag)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Etiqueta duplicada")
    db.refresh(tag)
    return tag


@router.delete("/{etiqueta_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_etiqueta(
    etiqueta_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador")),
):
    tag = db.get(Etiqueta, etiqueta_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Etiqueta no encontrada")
    db.delete(tag)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Etiqueta en uso")
    return None
