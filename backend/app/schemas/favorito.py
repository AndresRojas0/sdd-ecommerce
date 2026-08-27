"""Favorito schemas — RN-09."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class FavoritoResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
