"""Cart endpoints — RN-34 server-side, RN-12, RN-23."""
from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.base import get_db
from app.models.carrito import Carrito
from app.models.carrito_item import CarritoItem
from app.models.producto import Producto
from app.models.user import User
from app.schemas.carrito import CarritoItemCreate, CarritoItemUpdate, CarritoItemResponse, CarritoResponse

router = APIRouter(prefix="/carts", tags=["carts"])


def _get_or_create_cart(db: Session, user_id: uuid.UUID) -> Carrito:
    cart = db.scalar(select(Carrito).where(Carrito.user_id == user_id))
    if not cart:
        cart = Carrito(user_id=user_id)
        db.add(cart)
        db.flush()
    return cart


def _cart_response(db: Session, cart: Carrito) -> CarritoResponse:
    items = db.scalars(select(CarritoItem).where(CarritoItem.carrito_id == cart.id)).all()
    item_responses = []
    total = Decimal("0")
    for it in items:
        prod = db.get(Producto, it.product_id)
        total += it.subtotal
        item_responses.append(
            CarritoItemResponse(
                id=it.id,
                carrito_id=it.carrito_id,
                product_id=it.product_id,
                cantidad=it.cantidad,
                precio_unitario=it.precio_unitario,
                subtotal=it.subtotal,
                created_at=it.created_at,
                updated_at=it.updated_at,
                producto_titulo=prod.titulo if prod else None,
                producto_slug=prod.slug if prod else None,
            )
        )
    return CarritoResponse(
        id=cart.id,
        user_id=cart.user_id,
        created_at=cart.created_at,
        updated_at=cart.updated_at,
        items=item_responses,
        total=total,
    )


@router.get("/me", response_model=CarritoResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    cart = _get_or_create_cart(db, current_user.id)
    db.commit()
    db.refresh(cart)
    return _cart_response(db, cart)


@router.post("/me/items", response_model=CarritoItemResponse, status_code=status.HTTP_201_CREATED)
def add_item(
    body: CarritoItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    prod = db.get(Producto, body.product_id)
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    if prod.deleted_at is not None or prod.estado_publicacion != "publicado":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no disponible")
    cart = _get_or_create_cart(db, current_user.id)
    # Upsert
    existing = db.scalar(
        select(CarritoItem).where(CarritoItem.carrito_id == cart.id, CarritoItem.product_id == body.product_id)
    )
    if existing:
        existing.cantidad = body.cantidad
        existing.precio_unitario = prod.precio
        existing.subtotal = body.cantidad * prod.precio
        db.commit()
        db.refresh(existing)
        return CarritoItemResponse(
            id=existing.id,
            carrito_id=existing.carrito_id,
            product_id=existing.product_id,
            cantidad=existing.cantidad,
            precio_unitario=existing.precio_unitario,
            subtotal=existing.subtotal,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
            producto_titulo=prod.titulo,
            producto_slug=prod.slug,
        )
    item = CarritoItem(
        carrito_id=cart.id,
        product_id=body.product_id,
        cantidad=body.cantidad,
        precio_unitario=prod.precio,
        subtotal=body.cantidad * prod.precio,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return CarritoItemResponse(
        id=item.id,
        carrito_id=item.carrito_id,
        product_id=item.product_id,
        cantidad=item.cantidad,
        precio_unitario=item.precio_unitario,
        subtotal=item.subtotal,
        created_at=item.created_at,
        updated_at=item.updated_at,
        producto_titulo=prod.titulo,
        producto_slug=prod.slug,
    )


@router.put("/me/items/{item_id}", response_model=CarritoItemResponse)
def update_item(
    item_id: uuid.UUID,
    body: CarritoItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    cart = _get_or_create_cart(db, current_user.id)
    item = db.get(CarritoItem, item_id)
    if not item or item.carrito_id != cart.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado")
    prod = db.get(Producto, item.product_id)
    item.cantidad = body.cantidad
    if prod:
        item.precio_unitario = prod.precio
    item.subtotal = item.cantidad * item.precio_unitario
    db.commit()
    db.refresh(item)
    return CarritoItemResponse(
        id=item.id,
        carrito_id=item.carrito_id,
        product_id=item.product_id,
        cantidad=item.cantidad,
        precio_unitario=item.precio_unitario,
        subtotal=item.subtotal,
        created_at=item.created_at,
        updated_at=item.updated_at,
        producto_titulo=prod.titulo if prod else None,
        producto_slug=prod.slug if prod else None,
    )


@router.delete("/me/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    cart = _get_or_create_cart(db, current_user.id)
    item = db.get(CarritoItem, item_id)
    if not item or item.carrito_id != cart.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado")
    db.delete(item)
    db.commit()
    return None


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    cart = db.scalar(select(Carrito).where(Carrito.user_id == current_user.id))
    if cart:
        # delete items
        for it in db.scalars(select(CarritoItem).where(CarritoItem.carrito_id == cart.id)).all():
            db.delete(it)
        db.commit()
    return None
