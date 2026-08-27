"""PedidoItem model — data-model.md §14 (RN-26)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PedidoItem(Base):
    """Order line — price snapshot at confirmation."""

    __tablename__ = "pedido_items"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_pedido_items_cantidad"),
        CheckConstraint("precio_unitario > 0", name="ck_pedido_items_precio_unitario"),
        CheckConstraint("subtotal >= 0", name="ck_pedido_items_subtotal"),
        Index("idx_pedido_items_pedido_id", "pedido_id"),
        Index("idx_pedido_items_product_id", "product_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    pedido_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pedidos.id", ondelete="CASCADE"),
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

    pedido: Mapped[Pedido] = relationship("Pedido", back_populates="items")  # type: ignore[name-defined]
    producto: Mapped[Producto] = relationship("Producto")  # type: ignore[name-defined]
