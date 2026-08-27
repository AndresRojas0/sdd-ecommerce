"""Etiqueta schemas — RN-02, RN-03, RN-20."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class EtiquetaCreate(BaseModel):
    nombre: str
    slug: str


class EtiquetaResponse(BaseModel):
    id: uuid.UUID
    nombre: str
    slug: str
    created_at: datetime

    model_config = {"from_attributes": True}
