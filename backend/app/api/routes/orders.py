"""Orders / Pedidos — RN-18, RN-26, RN-28, RN-29, UC-B05..B08, UC-V06..09."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_role
from app.db.base import get_db
from app.models.carrito import Carrito
from app.models.carrito_item import CarritoItem
from app.models.orden_compra import OrdenCompra
from app.models.pedido import Pedido
from app.models.pedido_item import PedidoItem
from app.models.producto import Producto
from app.models.user import User
from app.schemas.pedido import (
    ConsolidateRequest,
    OrdenCompraResponse,
    PedidoItemResponse,
    PedidoResponse,
    ReassignRequest,
    RejectRequest,
)

router = APIRouter(prefix="/orders", tags=["orders"])
admin_router = APIRouter(prefix="/admin/orders", tags=["admin-orders"])
purchase_router = APIRouter(prefix="/admin/purchase-orders", tags=["purchase-orders"])


def _pedido_to_response(db: Session, pedido: Pedido) -> PedidoResponse:
    items = db.scalars(select(PedidoItem).where(PedidoItem.pedido_id == pedido.id)).all()
    item_resps = []
    for it in items:
        prod = db.get(Producto, it.product_id)
        item_resps.append(
            PedidoItemResponse(
                id=it.id,
                pedido_id=it.pedido_id,
                product_id=it.product_id,
                cantidad=it.cantidad,
                precio_unitario=it.precio_unitario,
                subtotal=it.subtotal,
                producto_titulo=prod.titulo if prod else None,
            )
        )
    return PedidoResponse(
        id=pedido.id,
        user_id=pedido.user_id,
        vendedor_id=pedido.vendedor_id,
        estado=pedido.estado,
        motivo_rechazo=pedido.motivo_rechazo,
        subtotal=pedido.subtotal,
        total=pedido.total,
        orden_compra_id=pedido.orden_compra_id,
        created_at=pedido.created_at,
        updated_at=pedido.updated_at,
        items=item_resps,
    )


def _generate_oc_numero(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    # Count existing OCs this year
    count = db.scalar(select(func.count()).select_from(OrdenCompra).where(OrdenCompra.numero.ilike(f"OC-{year}-%"))) or 0
    # Also ensure uniqueness via retry? Use count+1
    # To avoid race, we'll loop until unique
    for attempt in range(1, 100):
        numero = f"OC-{year}-{count + attempt:04d}"
        exists = db.scalar(select(OrdenCompra).where(OrdenCompra.numero == numero))
        if not exists:
            return numero
    # fallback uuid
    return f"OC-{year}-{uuid.uuid4().hex[:6].upper()}"


# ---------------------------------------------------------------------------
# Buyer orders
# ---------------------------------------------------------------------------


@router.post("", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    cart = db.scalar(select(Carrito).where(Carrito.user_id == current_user.id))
    if not cart:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Carrito vacío")
    cart_items = db.scalars(select(CarritoItem).where(CarritoItem.carrito_id == cart.id)).all()
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Carrito vacío")

    subtotal = sum((ci.subtotal for ci in cart_items), Decimal("0"))
    # Validate products still available
    for ci in cart_items:
        prod = db.get(Producto, ci.product_id)
        if not prod or prod.deleted_at is not None or prod.estado_publicacion != "publicado":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Producto {ci.product_id} no disponible")

    pedido = Pedido(
        user_id=current_user.id,
        vendedor_id=None,
        estado="pendiente",
        subtotal=subtotal,
        total=subtotal,
    )
    db.add(pedido)
    db.flush()
    for ci in cart_items:
        # Use current price snapshot
        prod = db.get(Producto, ci.product_id)
        price = prod.precio if prod else ci.precio_unitario
        pi = PedidoItem(
            pedido_id=pedido.id,
            product_id=ci.product_id,
            cantidad=ci.cantidad,
            precio_unitario=price,
            subtotal=ci.cantidad * price,
        )
        db.add(pi)
    # Clear cart items
    for ci in cart_items:
        db.delete(ci)
    db.commit()
    db.refresh(pedido)
    return _pedido_to_response(db, pedido)


@router.get("", response_model=dict)
def list_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    total = db.scalar(select(func.count()).select_from(Pedido).where(Pedido.user_id == current_user.id)) or 0
    pedidos = db.scalars(
        select(Pedido).where(Pedido.user_id == current_user.id).order_by(Pedido.created_at.desc()).limit(limit).offset(offset)
    ).all()
    items = [_pedido_to_response(db, p).model_dump() for p in pedidos]
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@router.get("/{pedido_id}", response_model=PedidoResponse)
def get_order(
    pedido_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    is_staff = current_user.role in ("vendedor", "administrador")
    if not is_staff and pedido.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return _pedido_to_response(db, pedido)


@router.put("/{pedido_id}", response_model=PedidoResponse)
def update_pending_order(
    pedido_id: uuid.UUID,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    if pedido.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    if pedido.estado != "pendiente":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Solo pedidos pendientes son editables (RN-28)")

    items_data = body.get("items")
    if items_data is not None:
        # Replace items: each item has product_id, cantidad
        # Validate
        new_subtotal = Decimal("0")
        # Delete old items
        db.execute(delete(PedidoItem).where(PedidoItem.pedido_id == pedido.id))
        for raw in items_data:
            pid = raw.get("product_id")
            cant = raw.get("cantidad")
            if not pid or cant is None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cada item requiere product_id y cantidad")
            try:
                pid_uuid = uuid.UUID(str(pid))
            except ValueError:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"product_id inválido {pid}")
            prod = db.get(Producto, pid_uuid)
            if not prod or prod.deleted_at is not None or prod.estado_publicacion != "publicado":
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Producto {pid} no disponible")
            cantidad = Decimal(str(cant))
            if cantidad <= 0:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="cantidad debe ser >0")
            price = prod.precio
            sub = cantidad * price
            new_subtotal += sub
            db.add(PedidoItem(pedido_id=pedido.id, product_id=pid_uuid, cantidad=cantidad, precio_unitario=price, subtotal=sub))
        pedido.subtotal = new_subtotal
        pedido.total = new_subtotal
    db.commit()
    db.refresh(pedido)
    return _pedido_to_response(db, pedido)


@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pending_order(
    pedido_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    if pedido.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    if pedido.estado != "pendiente":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Solo pendientes se pueden eliminar (RN-28)")
    db.delete(pedido)
    db.commit()
    return None


@router.post("/{pedido_id}/duplicate", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def duplicate_rejected(
    pedido_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    orig = db.get(Pedido, pedido_id)
    if not orig:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    if orig.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    if orig.estado != "rechazado":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Solo pedidos rechazados pueden duplicarse (RN-28)")

    new_pedido = Pedido(
        user_id=current_user.id,
        vendedor_id=None,
        estado="pendiente",
        subtotal=orig.subtotal,
        total=orig.total,
    )
    db.add(new_pedido)
    db.flush()
    items = db.scalars(select(PedidoItem).where(PedidoItem.pedido_id == orig.id)).all()
    for it in items:
        db.add(
            PedidoItem(
                pedido_id=new_pedido.id,
                product_id=it.product_id,
                cantidad=it.cantidad,
                precio_unitario=it.precio_unitario,
                subtotal=it.subtotal,
            )
        )
    db.commit()
    db.refresh(new_pedido)
    return _pedido_to_response(db, new_pedido)


# ---------------------------------------------------------------------------
# Admin / Vendedor operations
# ---------------------------------------------------------------------------


@admin_router.get("", response_model=dict)
def admin_list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("vendedor", "administrador")),
    estado: str | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
    vendedor_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    filters = []
    if estado:
        filters.append(Pedido.estado == estado)
    if user_id:
        filters.append(Pedido.user_id == user_id)
    if vendedor_id:
        filters.append(Pedido.vendedor_id == vendedor_id)
    base = select(Pedido)
    count_base = select(func.count()).select_from(Pedido)
    if filters:
        from sqlalchemy import and_

        base = base.where(and_(*filters))
        count_base = count_base.where(and_(*filters))
    total = db.scalar(count_base) or 0
    pedidos = db.scalars(base.order_by(Pedido.created_at.desc()).limit(limit).offset(offset)).all()
    items = [_pedido_to_response(db, p).model_dump() for p in pedidos]
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@admin_router.patch("/{pedido_id}/reassign", response_model=PedidoResponse)
def reassign_vendedor(
    pedido_id: uuid.UUID,
    body: ReassignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("administrador")),
):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    if pedido.estado != "pendiente":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Solo pedidos pendientes son reasignables (RN-27)")
    vendedor = db.get(User, body.to_vendedor_id)
    if not vendedor or vendedor.role not in ("vendedor", "administrador") or not vendedor.is_active:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Vendedor no válido")
    pedido.vendedor_id = body.to_vendedor_id
    # Audit log could be added; at minimum updated_at changes via trigger
    db.commit()
    db.refresh(pedido)
    return _pedido_to_response(db, pedido)


@admin_router.post("/{pedido_id}/accept", response_model=dict)
def accept_order(
    pedido_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("vendedor", "administrador")),
):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    if pedido.estado != "pendiente":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Solo pendientes pueden aceptarse")
    # Create OrdenCompra
    oc = OrdenCompra(
        numero=_generate_oc_numero(db),
        total=pedido.total,
        created_by=current_user.id,
    )
    db.add(oc)
    db.flush()
    pedido.estado = "aceptado"
    pedido.orden_compra_id = oc.id
    pedido.vendedor_id = pedido.vendedor_id or current_user.id
    db.commit()
    db.refresh(pedido)
    db.refresh(oc)
    return {"pedido": _pedido_to_response(db, pedido).model_dump(), "orden_compra": OrdenCompraResponse.model_validate(oc).model_dump()}


@admin_router.post("/{pedido_id}/reject", response_model=PedidoResponse)
def reject_order(
    pedido_id: uuid.UUID,
    body: RejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("vendedor", "administrador")),
):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    if pedido.estado != "pendiente":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Solo pendientes pueden rechazarse")
    if not body.motivo_rechazo or not body.motivo_rechazo.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="motivo_rechazo requerido")
    pedido.estado = "rechazado"
    pedido.motivo_rechazo = body.motivo_rechazo
    db.commit()
    db.refresh(pedido)
    return _pedido_to_response(db, pedido)


@admin_router.post("/consolidate", response_model=dict)
def consolidate_orders(
    body: ConsolidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("administrador")),
):
    if not body.pedido_ids or len(body.pedido_ids) < 2:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Se requieren al menos 2 pedidos")
    pedidos = []
    for pid in body.pedido_ids:
        p = db.get(Pedido, pid)
        if not p:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pedido {pid} no encontrado")
        pedidos.append(p)
    # All pending
    for p in pedidos:
        if p.estado != "pendiente":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Pedido {p.id} no está pendiente")
    # Same comprador
    user_ids = {p.user_id for p in pedidos}
    if len(user_ids) != 1:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Solo pedidos del mismo comprador pueden consolidarse (RN-29)")
    total = sum((p.total for p in pedidos), Decimal("0"))
    oc = OrdenCompra(
        numero=_generate_oc_numero(db),
        total=total,
        created_by=current_user.id,
    )
    db.add(oc)
    db.flush()
    for p in pedidos:
        p.estado = "aceptado"
        p.orden_compra_id = oc.id
    db.commit()
    db.refresh(oc)
    return {
        "orden_compra": OrdenCompraResponse.model_validate(oc).model_dump(),
        "pedidos": [_pedido_to_response(db, p).model_dump() for p in pedidos],
    }


# ---------------------------------------------------------------------------
# Purchase orders
# ---------------------------------------------------------------------------


@purchase_router.get("", response_model=dict)
def list_purchase_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("vendedor", "administrador")),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    total = db.scalar(select(func.count()).select_from(OrdenCompra)) or 0
    ocs = db.scalars(select(OrdenCompra).order_by(OrdenCompra.created_at.desc()).limit(limit).offset(offset)).all()
    items = [OrdenCompraResponse.model_validate(o).model_dump() for o in ocs]
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@purchase_router.get("/{oc_id}", response_model=dict)
def get_purchase_order(
    oc_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("vendedor", "administrador")),
):
    oc = db.get(OrdenCompra, oc_id)
    if not oc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden de compra no encontrada")
    pedidos = db.scalars(select(Pedido).where(Pedido.orden_compra_id == oc.id)).all()
    oc_data = OrdenCompraResponse.model_validate(oc).model_dump()
    oc_data["pedidos"] = [_pedido_to_response(db, p).model_dump() for p in pedidos]
    return oc_data
