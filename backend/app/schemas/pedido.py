"""Pedido / OrdenCompra schemas — RN-18, RN-26, RN-27, RN-28, RN-29."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PedidoItemResponse(BaseModel):
    id: uuid.UUID
    pedido_id: uuid.UUID
    product_id: uuid.UUID
    cantidad: Decimal
    precio_unitario: Decimal
    # ADR-008: precio de lista al momento del snapshot
    precio_lista: Decimal | None = None
    subtotal: Decimal
    producto_titulo: str | None = None

    model_config = {"from_attributes": True}


class PedidoResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    vendedor_id: uuid.UUID | None = None
    estado: str
    motivo_rechazo: str | None = None
    subtotal: Decimal
    total: Decimal
    orden_compra_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
    items: list[PedidoItemResponse] = []

    model_config = {"from_attributes": True}


class PedidoUpdateItemsRequest(BaseModel):
    items: list[dict]  # validated in handler: product_id, cantidad


class ReassignRequest(BaseModel):
    to_vendedor_id: uuid.UUID


class LineCantidadUpdate(BaseModel):
    line_id: uuid.UUID
    cantidad: Decimal


class LineAdd(BaseModel):
    product_id: uuid.UUID
    cantidad: Decimal


class PedidoEditLinesRequest(BaseModel):
    """A-PED-06: edición de líneas (solo pedidos `pendiente`).

    - updates: cambia `cantidad` de líneas existentes (por line_id)
    - remove: line_ids a eliminar
    - add: nuevas líneas {product_id, cantidad}
    """

    updates: list[LineCantidadUpdate] = []
    remove: list[uuid.UUID] = []
    add: list[LineAdd] = []


class RejectRequest(BaseModel):
    motivo_rechazo: str


class ConsolidateRequest(BaseModel):
    pedido_ids: list[uuid.UUID]


class CreateOrderOnBehalfRequest(BaseModel):
    user_id: uuid.UUID
    items: list[dict]  # cada item: product_id, cantidad — validado en handler (UC-V08)


class OrdenCompraResponse(BaseModel):
    id: uuid.UUID
    numero: str
    total: Decimal
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
    pedidos: list[PedidoResponse] | None = None

    model_config = {"from_attributes": True}
