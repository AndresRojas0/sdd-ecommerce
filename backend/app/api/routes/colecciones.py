"""Colecciones endpoints — RN-39, RN-20."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_optional_user, require_role
from app.db.base import get_db
from app.models.coleccion import Coleccion
from app.models.coleccion_producto import ColeccionProducto
from app.models.producto import Producto
from app.schemas.coleccion import (
    ColeccionCreate,
    ColeccionDetailResponse,
    ColeccionProductoAdd,
    ColeccionResponse,
    ColeccionUpdate,
    ReorderBody,
)

router = APIRouter(prefix="/colecciones", tags=["colecciones"])


def _to_response(col: Coleccion, count: int | None = None) -> dict:
    return {
        "id": col.id,
        "nombre": col.nombre,
        "slug": col.slug,
        "descripcion": col.descripcion,
        "imagen": col.imagen,
        "destacada": col.destacada,
        "created_at": col.created_at,
        "updated_at": col.updated_at,
        "productos_count": count,
    }


@router.get("", response_model=list[ColeccionResponse])
def list_colecciones(
    db: Session = Depends(get_db),
    destacada: bool | None = Query(default=None, description="Filtrar por destacada"),
    current_user=Depends(get_optional_user),
):
    stmt = select(Coleccion).order_by(Coleccion.created_at.desc())
    if destacada is not None:
        stmt = stmt.where(Coleccion.destacada == destacada)
    colecciones = db.scalars(stmt).all()
    result = []
    for col in colecciones:
        cnt = db.scalar(select(func.count()).select_from(ColeccionProducto).where(ColeccionProducto.coleccion_id == col.id))
        result.append(_to_response(col, cnt or 0))
    return result


@router.get("/{identifier}", response_model=ColeccionDetailResponse)
def get_coleccion(
    identifier: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    col = None
    try:
        cid = uuid.UUID(identifier)
        col = db.get(Coleccion, cid)
    except ValueError:
        pass
    if not col:
        col = db.scalar(select(Coleccion).where(Coleccion.slug == identifier))
    if not col:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colección no encontrada")
    # Load productos via join ordered by orden
    rows = db.execute(
        select(Producto, ColeccionProducto.orden, ColeccionProducto.added_at)
        .join(ColeccionProducto, ColeccionProducto.product_id == Producto.id)
        .where(ColeccionProducto.coleccion_id == col.id)
        .order_by(ColeccionProducto.orden.asc(), ColeccionProducto.added_at.asc())
    ).all()
    productos = []
    for prod, orden, added_at in rows:
        productos.append(
            {
                "id": prod.id,
                "titulo": prod.titulo,
                "slug": prod.slug,
                "precio": prod.precio,
                "imagen": prod.imagen,
                "orden": orden,
                "added_at": added_at,
            }
        )
    cnt = len(productos)
    data = _to_response(col, cnt)
    data["productos"] = productos
    return data


@router.post("", response_model=ColeccionResponse, status_code=status.HTTP_201_CREATED)
def create_coleccion(
    body: ColeccionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador")),
):
    col = Coleccion(
        nombre=body.nombre,
        slug=body.slug.lower(),
        descripcion=body.descripcion,
        imagen=body.imagen,
        destacada=body.destacada,
    )
    db.add(col)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nombre o slug duplicado")
    db.refresh(col)
    return _to_response(col, 0)


@router.put("/{coleccion_id}", response_model=ColeccionResponse)
def update_coleccion(
    coleccion_id: uuid.UUID,
    body: ColeccionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador")),
):
    col = db.get(Coleccion, coleccion_id)
    if not col:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colección no encontrada")
    if body.nombre is not None:
        col.nombre = body.nombre.strip()
    if body.slug is not None:
        col.slug = body.slug.strip().lower()
    if body.descripcion is not None:
        col.descripcion = body.descripcion
    # Allow explicit null for descripcion/imagen via model_fields_set detection
    if "descripcion" in body.model_fields_set and body.descripcion is None:
        col.descripcion = None
    if "imagen" in body.model_fields_set:
        col.imagen = body.imagen
    if body.destacada is not None:
        col.destacada = body.destacada
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nombre o slug duplicado")
    db.refresh(col)
    cnt = db.scalar(select(func.count()).select_from(ColeccionProducto).where(ColeccionProducto.coleccion_id == col.id)) or 0
    return _to_response(col, cnt)


@router.delete("/{coleccion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coleccion(
    coleccion_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador")),
):
    col = db.get(Coleccion, coleccion_id)
    if not col:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colección no encontrada")
    db.delete(col)
    db.commit()
    return None


@router.post("/{coleccion_id}/productos", status_code=status.HTTP_201_CREATED)
def add_producto_to_coleccion(
    coleccion_id: uuid.UUID,
    body: ColeccionProductoAdd,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador")),
):
    col = db.get(Coleccion, coleccion_id)
    if not col:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colección no encontrada")
    prod = db.get(Producto, body.product_id)
    if not prod:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Producto no existe")
    if prod.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Producto eliminado no puede agregarse")
    existing = db.get(ColeccionProducto, (coleccion_id, body.product_id))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Producto ya está en la colección")
    orden = body.orden if body.orden is not None else 0
    if orden < 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="orden debe ser >= 0")
    cp = ColeccionProducto(coleccion_id=coleccion_id, product_id=body.product_id, orden=orden)
    db.add(cp)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Error de integridad") from e
    return {"coleccion_id": str(coleccion_id), "product_id": str(body.product_id), "orden": orden}


@router.patch("/{coleccion_id}/productos/reorder", response_model=dict)
def reorder_productos(
    coleccion_id: uuid.UUID,
    body: ReorderBody,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador")),
):
    col = db.get(Coleccion, coleccion_id)
    if not col:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colección no encontrada")
    # Validate all product_ids exist and belong to collection or will be reordered? Spec says ordered list of product_ids to update orden
    # We update orden based on index in list for those product_ids that are in collection
    # If list contains product not in collection, ignore or 404? We'll 422 if any not in collection
    for idx, pid in enumerate(body.product_ids):
        cp = db.get(ColeccionProducto, (coleccion_id, pid))
        if not cp:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Producto {pid} no está en la colección")
        cp.orden = idx
    db.commit()
    return {"coleccion_id": str(coleccion_id), "ordered": [str(pid) for pid in body.product_ids]}


@router.delete("/{coleccion_id}/productos/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_producto_from_coleccion(
    coleccion_id: uuid.UUID,
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador")),
):
    cp = db.get(ColeccionProducto, (coleccion_id, product_id))
    if not cp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vínculo no encontrado")
    db.delete(cp)
    db.commit()
    return None
