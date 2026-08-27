"""Calificacion schemas — RN-21, RN-33."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class CalificacionCreate(BaseModel):
    estrellas: int

    @field_validator("estrellas")
    @classmethod
    def validate_stars(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("estrellas debe estar entre 1 y 5")
        return v


class CalificacionUpdate(BaseModel):
    estrellas: int

    @field_validator("estrellas")
    @classmethod
    def validate_stars(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("estrellas debe estar entre 1 y 5")
        return v


class CalificacionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    estrellas: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
