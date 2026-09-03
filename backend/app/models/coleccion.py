"""Coleccion model — data-model.md §8 (RN-39, RN-20)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Coleccion(Base):
    """Grupo curado transversal a categorías (RN-39)."""

    __tablename__ = "colecciones"
    __table_args__ = (
        Index("idx_colecciones_slug", "slug", unique=True),
        Index(
            "idx_colecciones_destacada",
            "destacada",
            postgresql_where=text("destacada = true"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    imagen: Mapped[str | None] = mapped_column(String(500), nullable=True)
    destacada: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
        default=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # Relationships
    productos: Mapped[list[ColeccionProducto]] = relationship(  # type: ignore[name-defined]
        "ColeccionProducto", back_populates="coleccion", cascade="all, delete-orphan"
    )
