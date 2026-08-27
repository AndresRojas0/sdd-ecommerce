"""ProductoEtiqueta join — data-model.md §7 (RN-02)."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProductoEtiqueta(Base):
    """N:M join — zero or more tags per product."""

    __tablename__ = "producto_etiquetas"
    __table_args__ = (
        Index("idx_pt_product_id", "product_id"),
        Index("idx_pt_etiqueta_id", "etiqueta_id"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    etiqueta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("etiquetas.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    )

    producto: Mapped[Producto] = relationship(  # type: ignore[name-defined]
        "Producto", back_populates="etiquetas"
    )
    etiqueta: Mapped[Etiqueta] = relationship(  # type: ignore[name-defined]
        "Etiqueta", back_populates="productos"
    )
