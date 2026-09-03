"""Categoria schemas — RN-01, RN-38, RN-20."""
from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


class CategoriaCreate(BaseModel):
    nombre: str
    slug: str
    color: str
    parent_id: uuid.UUID | None = None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        if not HEX_COLOR.match(v):
            raise ValueError("color debe ser hex #RRGGBB")
        return v

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


class CategoriaUpdate(BaseModel):
    nombre: str | None = None
    slug: str | None = None
    color: str | None = None
    parent_id: uuid.UUID | None = None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        if v is not None and not HEX_COLOR.match(v):
            raise ValueError("color debe ser hex #RRGGBB")
        return v


class CategoriaResponse(BaseModel):
    id: uuid.UUID
    nombre: str
    slug: str
    color: str
    parent_id: uuid.UUID | None = None
    nivel: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CategoriaTreeResponse(CategoriaResponse):
    """Respuesta árbol: raíz con hijas anidadas."""

    children: list[CategoriaResponse] = []
