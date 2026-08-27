"""CarritoItem model — data-model.md §12 (RN-23, RN-12)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CarritoItem(Base):
    """Cart line — quantity may be fractional (kg/m)."""

    __tablename__ = "carrito_items"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_carrito_items_cantidad"),
        CheckConstraint("precio_unitario > 0", name="ck_carrito_items_precio_unitario"),
        CheckConstraint("subtotal >= 0", name="ck_carrito_items_subtotal"),
        UniqueConstraint("carrito_id", "product_id", name="uq_carrito_items_carrito_product"),
        Index("idx_carrito_items_carrito_id", "carrito_id"),
        Index("idx_carrito_items_product_id", "product_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    carrito_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("carritos.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cantidad: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
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

    carrito: Mapped[Carrito] = relationship("Carrito", back_populates="items")  # type: ignore[name-defined]
    producto: Mapped[Producto] = relationship("Producto")  # type: ignore[name-defined]
