"""Etiqueta model — data-model.md §3 (RN-02, RN-03)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Etiqueta(Base):
    """Open vocabulary tag with trigram autocomplete (RN-02, RN-03)."""

    __tablename__ = "etiquetas"
    __table_args__ = (
        Index("idx_etiquetas_slug", "slug", unique=True),
        Index(
            "idx_etiquetas_nombre_trgm",
            "nombre",
            postgresql_using="gin",
            postgresql_ops={"nombre": "gin_trgm_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    productos: Mapped[list[ProductoEtiqueta]] = relationship(  # type: ignore[name-defined]
        "ProductoEtiqueta", back_populates="etiqueta", cascade="all, delete-orphan"
    )
