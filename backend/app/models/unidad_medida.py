"""UnidadMedida model — data-model.md §4 (RN-23)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UnidadMedida(Base):
    """Sale unit — open registry, extensible without redesign (RN-23)."""

    __tablename__ = "unidades_medida"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    simbolo: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    productos: Mapped[list[Producto]] = relationship(  # type: ignore[name-defined]
        "Producto", back_populates="unidad_venta"
    )
