"""Categorias endpoints — RN-01 (cerradas), RN-20 slugs."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_role
from app.db.base import get_db
from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate, CategoriaResponse, CategoriaUpdate

router = APIRouter(prefix="/categorias", tags=["categorias"])


@router.get("", response_model=list[CategoriaResponse])
def list_categorias(db: Session = Depends(get_db)):
    cats = db.scalars(select(Categoria).order_by(Categoria.nombre)).all()
    return cats


@router.post("", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
def create_categoria(
    body: CategoriaCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador")),
):
    cat = Categoria(nombre=body.nombre, slug=body.slug, color=body.color)
    db.add(cat)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nombre o slug duplicado")
    db.refresh(cat)
    return cat


@router.put("/{categoria_id}", response_model=CategoriaResponse)
def update_categoria(
    categoria_id: uuid.UUID,
    body: CategoriaUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador")),
):
    cat = db.get(Categoria, categoria_id)
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    if body.nombre is not None:
        cat.nombre = body.nombre
    if body.slug is not None:
        cat.slug = body.slug.lower()
    if body.color is not None:
        cat.color = body.color
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nombre o slug duplicado")
    db.refresh(cat)
    return cat


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_categoria(
    categoria_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador")),
):
    cat = db.get(Categoria, categoria_id)
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    try:
        db.delete(cat)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Categoría en uso por productos")
    return None
