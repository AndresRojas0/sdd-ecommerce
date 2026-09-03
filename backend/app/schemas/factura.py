"""Factura / Stock schemas — RN-35, RN-36, RN-37."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class FacturaResponse(BaseModel):
    id: uuid.UUID
    orden_compra_id: uuid.UUID
    numero_fiscal: str
    total: Decimal
    created_by: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class StockResponse(BaseModel):
    product_id: uuid.UUID
    cantidad_disponible: Decimal
    cantidad_reservada: Decimal
    updated_at: datetime

    model_config = {"from_attributes": True}


class MovimientoStockResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    tipo: str
    cantidad: Decimal
    pedido_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class StockUpdateRequest(BaseModel):
    cantidad_disponible: Decimal | None = None
    cantidad_reservada: Decimal | None = None
