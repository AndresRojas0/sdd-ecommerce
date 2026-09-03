"""ColeccionProducto join — data-model.md §9 (RN-39)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ColeccionProducto(Base):
    """N:M join — colección curada con productos y orden opcional (RN-39)."""

    __tablename__ = "coleccion_productos"
    __table_args__ = (
        CheckConstraint("orden IS NULL OR orden >= 0", name="ck_coleccion_productos_orden"),
        Index("idx_cp_coleccion_id", "coleccion_id"),
        Index("idx_cp_product_id", "product_id"),
        Index("idx_cp_coleccion_orden", "coleccion_id", "orden"),
    )

    coleccion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("colecciones.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    orden: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        server_default=text("0"),
        default=0,
    )

    coleccion: Mapped[Coleccion] = relationship(  # type: ignore[name-defined]
        "Coleccion", back_populates="productos"
    )
    producto: Mapped[Producto] = relationship("Producto")  # type: ignore[name-defined]
