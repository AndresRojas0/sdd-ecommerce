"""Carrito schemas — RN-12, RN-23, RN-34."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator


class CarritoItemCreate(BaseModel):
    product_id: uuid.UUID
    cantidad: Decimal

    @field_validator("cantidad")
    @classmethod
    def validate_cantidad(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("cantidad debe ser > 0")
        return v


class CarritoItemUpdate(BaseModel):
    cantidad: Decimal

    @field_validator("cantidad")
    @classmethod
    def validate_cantidad(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("cantidad debe ser > 0")
        return v


class CarritoItemResponse(BaseModel):
    id: uuid.UUID
    carrito_id: uuid.UUID
    product_id: uuid.UUID
    cantidad: Decimal
    precio_unitario: Decimal
    subtotal: Decimal
    created_at: datetime
    updated_at: datetime
    producto_titulo: str | None = None
    producto_slug: str | None = None

    model_config = {"from_attributes": True}


class CarritoResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    items: list[CarritoItemResponse] = []
    total: Decimal = Decimal("0")

    model_config = {"from_attributes": True}
