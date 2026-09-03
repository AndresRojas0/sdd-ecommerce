"""Product schemas — RN-01, RN-11, RN-13, RN-20, RN-23, RN-31."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator


class ProductCreate(BaseModel):
    titulo: str
    slug: str
    descripcion: str | None = None
    componentes_incluidos: str | None = None
    datos_tecnicos: dict[str, Any] | None = None
    precio: Decimal
    imagen: str | None = None
    unidad_venta_id: uuid.UUID
    categoria_ids: list[uuid.UUID]
    etiqueta_ids: list[uuid.UUID] | None = None

    @field_validator("precio")
    @classmethod
    def validate_precio(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("precio debe ser > 0")
        return v

    @field_validator("categoria_ids")
    @classmethod
    def validate_cats(cls, v: list[uuid.UUID]) -> list[uuid.UUID]:
        if not v or len(v) < 1:
            raise ValueError("al menos una categoría requerida (RN-01)")
        return v


class ProductUpdate(BaseModel):
    titulo: str | None = None
    slug: str | None = None
    descripcion: str | None = None
    componentes_incluidos: str | None = None
    datos_tecnicos: dict[str, Any] | None = None
    precio: Decimal | None = None
    imagen: str | None = None
    unidad_venta_id: uuid.UUID | None = None
    categoria_ids: list[uuid.UUID] | None = None
    etiqueta_ids: list[uuid.UUID] | None = None

    @field_validator("precio")
    @classmethod
    def validate_precio(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("precio debe ser > 0")
        return v


class CategoriaBrief(BaseModel):
    id: uuid.UUID
    nombre: str
    slug: str
    color: str
    parent_id: uuid.UUID | None = None
    nivel: int | None = None

    model_config = {"from_attributes": True}


class EtiquetaBrief(BaseModel):
    id: uuid.UUID
    nombre: str
    slug: str

    model_config = {"from_attributes": True}


class UnidadBrief(BaseModel):
    id: uuid.UUID
    nombre: str
    simbolo: str

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    id: uuid.UUID
    titulo: str
    slug: str
    descripcion: str | None = None
    componentes_incluidos: str | None = None
    datos_tecnicos: dict[str, Any] | None = None
    precio: Decimal
    imagen: str | None = None
    unidad_venta_id: uuid.UUID
    unidad_venta: UnidadBrief | None = None
    categorias: list[CategoriaBrief] = []
    etiquetas: list[EtiquetaBrief] = []
    estado_publicacion: str
    deleted_at: datetime | None = None
    visitas_count: int
    guardados_count: int
    busquedas_count: int
    calificacion_promedio: Decimal
    calificacion_cantidad: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductStatsResponse(BaseModel):
    producto_id: uuid.UUID
    visitas_count: int
    guardados_count: int
    busquedas_count: int
    calificacion_promedio: Decimal
    calificacion_cantidad: int
