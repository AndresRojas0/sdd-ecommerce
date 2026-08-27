"""Favorites — RN-09 counter, RN-06 auth, UC-B03."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.base import get_db
from app.models.favorito import Favorito
from app.models.producto import Producto
from app.models.user import User

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.post("/{product_id}", status_code=status.HTTP_201_CREATED)
def add_favorite(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    prod = db.get(Producto, product_id)
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    if prod.deleted_at is not None or prod.estado_publicacion != "publicado":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no disponible")

    existing = db.scalar(
        select(Favorito).where(Favorito.user_id == current_user.id, Favorito.product_id == product_id)
    )
    if existing:
        return {"message": "Ya en favoritos", "id": str(existing.id)}

    fav = Favorito(user_id=current_user.id, product_id=product_id)
    db.add(fav)
    # Increment counter transactionally
    prod.guardados_count = (prod.guardados_count or 0) + 1
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Favorito duplicado") from e
    db.refresh(fav)
    return {"message": "Favorito agregado", "id": str(fav.id)}


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
def remove_favorite(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    fav = db.scalar(
        select(Favorito).where(Favorito.user_id == current_user.id, Favorito.product_id == product_id)
    )
    if not fav:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorito no encontrado")
    prod = db.get(Producto, product_id)
    db.delete(fav)
    if prod:
        prod.guardados_count = max(0, (prod.guardados_count or 1) - 1)
    db.commit()
    return {"message": "Favorito eliminado"}


@router.get("", response_model=list[dict])
def list_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    favs = db.scalars(select(Favorito).where(Favorito.user_id == current_user.id)).all()
    result = []
    for f in favs:
        prod = db.get(Producto, f.product_id)
        result.append(
            {
                "favorito_id": str(f.id),
                "product_id": str(f.product_id),
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "producto": {
                    "id": str(prod.id),
                    "titulo": prod.titulo,
                    "slug": prod.slug,
                    "precio": str(prod.precio),
                    "imagen": prod.imagen,
                }
                if prod
                else None,
            }
        )
    return result
