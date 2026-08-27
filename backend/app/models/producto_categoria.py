"""ProductoCategoria join — data-model.md §6 (RN-01)."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProductoCategoria(Base):
    """N:M join — a product belongs to one or more categories."""

    __tablename__ = "producto_categorias"
    __table_args__ = (
        Index("idx_pc_product_id", "product_id"),
        Index("idx_pc_categoria_id", "categoria_id"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    categoria_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categorias.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    )

    producto: Mapped[Producto] = relationship(  # type: ignore[name-defined]
        "Producto", back_populates="categorias"
    )
    categoria: Mapped[Categoria] = relationship(  # type: ignore[name-defined]
        "Categoria", back_populates="productos"
    )
