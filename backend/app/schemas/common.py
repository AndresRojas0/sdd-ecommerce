"""Common schemas: pagination, error."""
from __future__ import annotations

from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list  # overridden in subclasses
