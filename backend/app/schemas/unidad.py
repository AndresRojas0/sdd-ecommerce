"""UnidadMedida schemas — RN-23."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class UnidadCreate(BaseModel):
    nombre: str
    simbolo: str


class UnidadResponse(BaseModel):
    id: uuid.UUID
    nombre: str
    simbolo: str
    created_at: datetime

    model_config = {"from_attributes": True}
