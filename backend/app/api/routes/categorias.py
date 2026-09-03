"""Categorias endpoints — RN-01 (árbol 2N), RN-38, RN-20 slugs."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_role
from app.db.base import get_db
from app.models.categoria import Categoria
from app.models.producto_categoria import ProductoCategoria
from app.schemas.categoria import CategoriaCreate, CategoriaResponse, CategoriaTreeResponse, CategoriaUpdate

router = APIRouter(prefix="/categorias", tags=["categorias"])


def _to_response(cat: Categoria) -> dict:
    return {
        "id": cat.id,
        "nombre": cat.nombre,
        "slug": cat.slug,
        "color": cat.color,
        "parent_id": cat.parent_id,
        "nivel": cat.nivel,
        "created_at": cat.created_at,
        "updated_at": cat.updated_at,
    }


def _build_tree(cats: list[Categoria]) -> list[dict]:
    """Construye árbol 2 niveles: raíces (nivel 1) con children."""
    by_id = {c.id: _to_response(c) for c in cats}
    # Add children list to each
    for v in by_id.values():
        v["children"] = []
    roots: list[dict] = []
    for cat in cats:
        node = by_id[cat.id]
        if cat.parent_id is None:
            roots.append(node)
        else:
            parent = by_id.get(cat.parent_id)
            if parent is not None:
                parent["children"].append(node)
            else:
                # parent not in list (orphan) -> treat as root fallback
                roots.append(node)
    # Sort roots and children by nombre
    roots.sort(key=lambda x: x["nombre"])
    for r in roots:
        r["children"].sort(key=lambda x: x["nombre"])
    return roots


@router.get("", response_model=list[CategoriaResponse] | list[CategoriaTreeResponse])
def list_categorias(
    db: Session = Depends(get_db),
    include_children: bool = Query(default=False, description="Si true, retorna árbol anidado"),
    tree: bool = Query(default=False, description="Alias de include_children"),
):
    want_tree = include_children or tree
    cats = db.scalars(select(Categoria).order_by(Categoria.nombre)).all()
    if want_tree:
        return _build_tree(list(cats))
    return [_to_response(c) for c in cats]


@router.get("/{identifier}", response_model=CategoriaResponse | CategoriaTreeResponse)
def get_categoria(
    identifier: str,
    db: Session = Depends(get_db),
    include_children: bool = Query(default=False),
):
    cat = None
    try:
        cid = uuid.UUID(identifier)
        cat = db.get(Categoria, cid)
    except ValueError:
        pass
    if not cat:
        cat = db.scalar(select(Categoria).where(Categoria.slug == identifier))
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    data = _to_response(cat)
    if include_children:
        children = db.scalars(select(Categoria).where(Categoria.parent_id == cat.id).order_by(Categoria.nombre)).all()
        data["children"] = [_to_response(ch) for ch in children]
        return data
    return data


@router.post("", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
def create_categoria(
    body: CategoriaCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador")),
):
    nivel = 1
    if body.parent_id is not None:
        parent = db.get(Categoria, body.parent_id)
        if not parent:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="parent_id no existe")
        if parent.nivel != 1:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="parent_id debe apuntar a categoría nivel 1 (profundidad máx. 2)")
        nivel = 2
    # Prevent self-reference (not possible on create since id unknown, but validate in update)
    cat = Categoria(
        nombre=body.nombre,
        slug=body.slug.lower(),
        color=body.color,
        parent_id=body.parent_id,
        nivel=nivel,
    )
    db.add(cat)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nombre o slug duplicado")
    db.refresh(cat)
    return _to_response(cat)


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
    # parent_id update — need to detect if field was provided (including explicit null)
    # Pydantic sets parent_id to None if not provided OR if explicitly null; use model_fields_set
    if "parent_id" in body.model_fields_set:
        new_parent_id = body.parent_id
        if new_parent_id == cat.id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="parent_id no puede ser sí mismo")
        if new_parent_id is None:
            cat.parent_id = None
            cat.nivel = 1
        else:
            parent = db.get(Categoria, new_parent_id)
            if not parent:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="parent_id no existe")
            if parent.nivel != 1:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="parent_id debe apuntar a categoría nivel 1")
            # Prevent cycle: parent cannot be descendant of cat (only 2 levels so check if parent's parent is cat, or descendant check)
            # Since max depth 2, only cycle possible is cat -> child -> cat. Check if any child of cat is the parent.
            is_descendant = db.scalar(select(Categoria.id).where(Categoria.parent_id == cat.id, Categoria.id == new_parent_id))
            if is_descendant:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Ciclo detectado: parent_id es descendiente")
            # If cat currently has children (nivel 1 with hijos), it cannot become nivel 2
            has_children = db.scalar(select(Categoria.id).where(Categoria.parent_id == cat.id).limit(1))
            if has_children is not None:
                # Determine if has_children returned row; scalar returns id or None
                # If cat has children, moving it to nivel 2 would create depth 3 for its children, not allowed
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No se puede mover una categoría con subcategorías a nivel 2")
            cat.parent_id = new_parent_id
            cat.nivel = 2
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nombre o slug duplicado")
    db.refresh(cat)
    return _to_response(cat)


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_categoria(
    categoria_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("administrador")),
):
    cat = db.get(Categoria, categoria_id)
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    # RESTRICT checks before delete to provide 409 mapping
    has_children = db.scalar(select(Categoria.id).where(Categoria.parent_id == cat.id).limit(1))
    if has_children is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Categoría tiene subcategorías, no se puede eliminar")
    # Check product association
    has_products = db.scalar(select(ProductoCategoria.categoria_id).where(ProductoCategoria.categoria_id == cat.id).limit(1))
    if has_products is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Categoría en uso por productos")
    try:
        db.delete(cat)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Categoría en uso, no se puede eliminar (RESTRICT)")
    return None
