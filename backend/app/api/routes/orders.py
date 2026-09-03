"""Orders / Pedidos — RN-18, RN-26, RN-28, RN-29, RN-35, RN-36, RN-37, UC-B05..B08, UC-V06..09."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_role
from app.db.base import get_db
from app.models.carrito import Carrito
from app.models.carrito_item import CarritoItem
from app.models.factura import Factura
from app.models.movimiento_stock import MovimientoStock
from app.models.orden_compra import OrdenCompra
from app.models.pedido import Pedido
from app.models.pedido_item import PedidoItem
from app.models.producto import Producto
from app.models.stock import Stock
from app.models.user import User
from app.schemas.pedido import (
    ConsolidateRequest,
    CreateOrderOnBehalfRequest,
    OrdenCompraResponse,
    PedidoItemResponse,
    PedidoResponse,
    ReassignRequest,
    RejectRequest,
)

router = APIRouter(prefix="/orders", tags=["orders"])
admin_router = APIRouter(prefix="/admin/orders", tags=["admin-orders"])
purchase_router = APIRouter(prefix="/admin/purchase-orders", tags=["purchase-orders"])
stock_router = APIRouter(prefix="/admin/stock", tags=["admin-stock"])
dashboard_router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])


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
    count = db.scalar(select(func.count()).select_from(OrdenCompra).where(OrdenCompra.numero.ilike(f"OC-{year}-%"))) or 0
    for attempt in range(1, 100):
        numero = f"OC-{year}-{count + attempt:04d}"
        exists = db.scalar(select(OrdenCompra).where(OrdenCompra.numero == numero))
        if not exists:
            return numero
    return f"OC-{year}-{uuid.uuid4().hex[:6].upper()}"


def _generate_factura_numero(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    count = db.scalar(select(func.count()).select_from(Factura).where(Factura.numero_fiscal.ilike(f"F-{year}-%"))) or 0
    for attempt in range(1, 100):
        numero = f"F-{year}-{count + attempt:04d}"
        exists = db.scalar(select(Factura).where(Factura.numero_fiscal == numero))
        if not exists:
            return numero
    return f"F-{year}-{uuid.uuid4().hex[:6].upper()}"


def _get_or_create_stock(db: Session, product_id: uuid.UUID) -> Stock:
    stock = db.get(Stock, product_id)
    if stock is None:
        # Use set to ensure row exists even if concurrent — flush will handle unique
        stock = Stock(product_id=product_id, cantidad_disponible=Decimal("0"), cantidad_reservada=Decimal("0"))
        db.add(stock)
        db.flush()
    return db.get(Stock, product_id)  # re-fetch to ensure managed


def _reserve_stock_for_pedido(db: Session, pedido: Pedido) -> None:
    """RN-35 reserva: disponible -= cantidad, reservada += cantidad, movimiento reserva."""
    items = db.scalars(select(PedidoItem).where(PedidoItem.pedido_id == pedido.id)).all()
    for it in items:
        stock = _get_or_create_stock(db, it.product_id)
        # Check stock
        if stock.cantidad_disponible < it.cantidad:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Stock insuficiente para producto {it.product_id} (disponible {stock.cantidad_disponible}, requerido {it.cantidad})",
            )
        stock.cantidad_disponible = stock.cantidad_disponible - it.cantidad
        stock.cantidad_reservada = stock.cantidad_reservada + it.cantidad
        # Update timestamp
        stock.updated_at = datetime.now(timezone.utc)
        db.add(
            MovimientoStock(
                product_id=it.product_id,
                tipo="reserva",
                cantidad=it.cantidad,
                pedido_id=pedido.id,
            )
        )
    db.flush()


def _confirm_stock_for_pedido(db: Session, pedido: Pedido) -> None:
    """RN-35 confirmación: reservada -= cantidad, movimiento confirmacion."""
    items = db.scalars(select(PedidoItem).where(PedidoItem.pedido_id == pedido.id)).all()
    for it in items:
        stock = _get_or_create_stock(db, it.product_id)
        if stock.cantidad_reservada < it.cantidad:
            # If inconsistent, clamp to 0 but still record
            stock.cantidad_reservada = Decimal("0")
        else:
            stock.cantidad_reservada = stock.cantidad_reservada - it.cantidad
        stock.updated_at = datetime.now(timezone.utc)
        db.add(
            MovimientoStock(
                product_id=it.product_id,
                tipo="confirmacion",
                cantidad=it.cantidad,
                pedido_id=pedido.id,
            )
        )
    db.flush()


def _devolucion_stock_for_pedido(db: Session, pedido: Pedido) -> None:
    """RN-35 devolución: disponible += cantidad, reservada -= cantidad."""
    items = db.scalars(select(PedidoItem).where(PedidoItem.pedido_id == pedido.id)).all()
    for it in items:
        stock = _get_or_create_stock(db, it.product_id)
        stock.cantidad_disponible = stock.cantidad_disponible + it.cantidad
        if stock.cantidad_reservada >= it.cantidad:
            stock.cantidad_reservada = stock.cantidad_reservada - it.cantidad
        else:
            stock.cantidad_reservada = Decimal("0")
        stock.updated_at = datetime.now(timezone.utc)
        db.add(
            MovimientoStock(
                product_id=it.product_id,
                tipo="devolucion",
                cantidad=it.cantidad,
                pedido_id=pedido.id,
            )
        )
    db.flush()


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
        new_subtotal = Decimal("0")
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


@admin_router.post("", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def create_order_on_behalf(
    body: CreateOrderOnBehalfRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("vendedor", "administrador")),
):
    """UC-V08: Vendedor crea pedido en nombre de un cliente."""
    cliente = db.get(User, body.user_id)
    if not cliente or not cliente.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado o inactivo")
    if not body.items or len(body.items) == 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Se requiere al menos un item")

    subtotal = Decimal("0")
    validated: list[tuple[uuid.UUID, Decimal, Decimal]] = []
    for raw in body.items:
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
        validated.append((pid_uuid, cantidad, price))
        subtotal += cantidad * price

    pedido = Pedido(
        user_id=cliente.id,
        vendedor_id=current_user.id,
        estado="pendiente",
        subtotal=subtotal,
        total=subtotal,
    )
    db.add(pedido)
    db.flush()
    for pid_uuid, cantidad, price in validated:
        db.add(
            PedidoItem(
                pedido_id=pedido.id,
                product_id=pid_uuid,
                cantidad=cantidad,
                precio_unitario=price,
                subtotal=cantidad * price,
            )
        )
    db.commit()
    db.refresh(pedido)
    return _pedido_to_response(db, pedido)


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
    # Stock reservation (RN-35) — in same transaction
    # Must succeed before creating OC
    _reserve_stock_for_pedido(db, pedido)
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
    if pedido.estado not in ("pendiente", "aceptado"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Solo pendientes o aceptados pueden rechazarse")
    if not body.motivo_rechazo or not body.motivo_rechazo.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="motivo_rechazo requerido")
    # If aceptado, release reservation (RN-35 devolucion)
    if pedido.estado == "aceptado":
        _devolucion_stock_for_pedido(db, pedido)
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
    for p in pedidos:
        if p.estado != "pendiente":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Pedido {p.id} no está pendiente")
    user_ids = {p.user_id for p in pedidos}
    if len(user_ids) != 1:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Solo pedidos del mismo comprador pueden consolidarse (RN-29)")
    # Reserve stock for all pedidos before creating OC
    for p in pedidos:
        _reserve_stock_for_pedido(db, p)
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
# Extended flow — RN-28, RN-35, RN-36
# ---------------------------------------------------------------------------


@admin_router.post("/{pedido_id}/facturar", response_model=dict)
def facturar_order(
    pedido_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("administrador")),
):
    """Facturar OC via pedido: aceptado -> facturado + confirmación stock + factura."""
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    if pedido.estado != "aceptado":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Solo pedidos aceptados pueden facturarse (RN-28)")
    if not pedido.orden_compra_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Pedido sin orden de compra asociada")
    oc = db.get(OrdenCompra, pedido.orden_compra_id)
    if not oc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden de compra no encontrada")
    existing_factura = db.scalar(select(Factura).where(Factura.orden_compra_id == oc.id))
    if existing_factura:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La orden de compra ya está facturada (RN-36)")
    # All pedidos in OC must be aceptado
    oc_pedidos = db.scalars(select(Pedido).where(Pedido.orden_compra_id == oc.id)).all()
    for p in oc_pedidos:
        if p.estado != "aceptado":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Pedido {p.id} no está aceptado; todos los pedidos de la OC deben estar aceptados")

    total = sum((p.total for p in oc_pedidos), Decimal("0"))
    factura = Factura(
        orden_compra_id=oc.id,
        numero_fiscal=_generate_factura_numero(db),
        total=total,
        created_by=current_user.id,
    )
    db.add(factura)
    db.flush()

    for p in oc_pedidos:
        _confirm_stock_for_pedido(db, p)
        p.estado = "facturado"
    db.commit()
    db.refresh(factura)
    # Build response with updated pedidos
    pedidos_resp = [_pedido_to_response(db, p).model_dump() for p in db.scalars(select(Pedido).where(Pedido.orden_compra_id == oc.id)).all()]
    return {
        "factura": {
            "id": str(factura.id),
            "orden_compra_id": str(factura.orden_compra_id),
            "numero_fiscal": factura.numero_fiscal,
            "total": str(factura.total),
            "created_by": str(factura.created_by) if factura.created_by else None,
            "created_at": factura.created_at.isoformat() if factura.created_at else None,
        },
        "pedidos": pedidos_resp,
        "orden_compra": OrdenCompraResponse.model_validate(oc).model_dump(),
    }


@admin_router.post("/{pedido_id}/en-logistica", response_model=PedidoResponse)
def en_logistica_order(
    pedido_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("vendedor", "administrador")),
):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    if pedido.estado != "facturado":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Solo pedidos facturados pueden pasar a en_logistica (RN-28)")
    pedido.estado = "en_logistica"
    db.commit()
    db.refresh(pedido)
    return _pedido_to_response(db, pedido)


@admin_router.post("/{pedido_id}/entregar", response_model=PedidoResponse)
def entregar_order(
    pedido_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("vendedor", "administrador")),
):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    if pedido.estado != "en_logistica":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Solo pedidos en_logistica pueden entregarse (RN-28)")
    pedido.estado = "entregado"
    db.commit()
    db.refresh(pedido)
    return _pedido_to_response(db, pedido)


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


# ---------------------------------------------------------------------------
# Stock admin
# ---------------------------------------------------------------------------


@stock_router.get("", response_model=dict)
def list_stock(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("vendedor", "administrador")),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    total = db.scalar(select(func.count()).select_from(Stock)) or 0
    rows = db.scalars(select(Stock).order_by(Stock.product_id).limit(limit).offset(offset)).all()
    items = [
        {
            "product_id": str(s.product_id),
            "cantidad_disponible": str(s.cantidad_disponible),
            "cantidad_reservada": str(s.cantidad_reservada),
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in rows
    ]
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@stock_router.get("/{product_id}", response_model=dict)
def get_stock(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("vendedor", "administrador")),
):
    stock = db.get(Stock, product_id)
    if not stock:
        # Auto-create zero row for existing product (idempotent)
        prod = db.get(Producto, product_id)
        if not prod:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
        stock = Stock(product_id=product_id, cantidad_disponible=Decimal("0"), cantidad_reservada=Decimal("0"))
        db.add(stock)
        db.commit()
        db.refresh(stock)
    return {
        "product_id": str(stock.product_id),
        "cantidad_disponible": str(stock.cantidad_disponible),
        "cantidad_reservada": str(stock.cantidad_reservada),
        "updated_at": stock.updated_at.isoformat() if stock.updated_at else None,
    }


@stock_router.put("/{product_id}", response_model=dict)
def update_stock(
    product_id: uuid.UUID,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("administrador")),
):
    """Manual ajuste de stock — tipo ajuste (RN-35)."""
    prod = db.get(Producto, product_id)
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    stock = _get_or_create_stock(db, product_id)
    if "cantidad_disponible" in body:
        try:
            val = Decimal(str(body["cantidad_disponible"]))
        except Exception:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="cantidad_disponible inválida")
        if val < 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="cantidad_disponible debe ser >=0")
        diff = val - stock.cantidad_disponible
        if diff != 0:
            db.add(
                MovimientoStock(
                    product_id=product_id,
                    tipo="ajuste",
                    cantidad=abs(diff),
                    pedido_id=None,
                )
            )
        stock.cantidad_disponible = val
    if "cantidad_reservada" in body:
        try:
            val = Decimal(str(body["cantidad_reservada"]))
        except Exception:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="cantidad_reservada inválida")
        if val < 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="cantidad_reservada debe ser >=0")
        stock.cantidad_reservada = val
    stock.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(stock)
    return {
        "product_id": str(stock.product_id),
        "cantidad_disponible": str(stock.cantidad_disponible),
        "cantidad_reservada": str(stock.cantidad_reservada),
        "updated_at": stock.updated_at.isoformat() if stock.updated_at else None,
    }


# ---------------------------------------------------------------------------
# Dashboard totales del día — RN-37
# ---------------------------------------------------------------------------


@dashboard_router.get("/totales-hoy", response_model=dict)
def totales_hoy(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("vendedor", "administrador")),
):
    """RN-37: suma de facturas.total cuya created_at cae en el día corriente."""
    # Use DB date comparison compatible with both PG and SQLite
    today = date.today()
    # Approach: filter where created_at >= today 00:00 and < tomorrow
    start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    # Use naive truncate via func.date when available, but for SQLite we compare string
    # Simplest: SUM where DATE(created_at) = today — use func.date
    # For PG: created_at::date = CURRENT_DATE ; for SQLite: date(created_at)
    try:
        total = db.scalar(
            select(func.coalesce(func.sum(Factura.total), 0)).where(func.date(Factura.created_at) == today)
        )
    except Exception:
        db.rollback()
        facturas = db.scalars(select(Factura)).all()
        total = sum((f.total for f in facturas if f.created_at and f.created_at.date() == today), Decimal("0"))
    if total is None:
        total = Decimal("0")
    try:
        count = db.scalar(
            select(func.count()).select_from(Factura).where(func.date(Factura.created_at) == today)
        ) or 0
    except Exception:
        db.rollback()
        facturas = db.scalars(select(Factura)).all()
        count = sum(1 for f in facturas if f.created_at and f.created_at.date() == today)
    return {"fecha": today.isoformat(), "total": str(total), "cantidad_facturas": count}
