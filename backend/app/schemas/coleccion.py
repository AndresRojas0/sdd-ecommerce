"""Coleccion schemas — RN-39, RN-20."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class ColeccionCreate(BaseModel):
    nombre: str
    slug: str
    descripcion: str | None = None
    imagen: str | None = None
    destacada: bool = False

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("nombre requerido")
        return v.strip()

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("slug requerido")
        return v.strip().lower()


class ColeccionUpdate(BaseModel):
    nombre: str | None = None
    slug: str | None = None
    descripcion: str | None = None
    imagen: str | None = None
    destacada: bool | None = None


class ColeccionProductoAdd(BaseModel):
    product_id: uuid.UUID
    orden: int | None = 0

    @field_validator("orden")
    @classmethod
    def validate_orden(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("orden debe ser >= 0")
        return v


class ReorderBody(BaseModel):
    product_ids: list[uuid.UUID]


class ProductoColeccionBrief(BaseModel):
    id: uuid.UUID
    titulo: str
    slug: str
    precio: str | float | int
    imagen: str | None = None
    orden: int | None = None
    added_at: datetime | None = None

    model_config = {"from_attributes": True}


class ColeccionResponse(BaseModel):
    id: uuid.UUID
    nombre: str
    slug: str
    descripcion: str | None = None
    imagen: str | None = None
    destacada: bool
    created_at: datetime
    updated_at: datetime
    productos_count: int | None = None

    model_config = {"from_attributes": True}


class ColeccionDetailResponse(ColeccionResponse):
    productos: list[ProductoColeccionBrief] = []
