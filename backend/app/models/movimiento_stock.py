"""MovimientoStock model — data-model.md §16.2 (RN-35)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MovimientoStock(Base):
    """Historial auditable de cambios de stock (RN-35)."""

    __tablename__ = "movimientos_stock"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('reserva', 'confirmacion', 'devolucion', 'ajuste')",
            name="ck_mov_stock_tipo",
        ),
        CheckConstraint("cantidad > 0", name="ck_mov_stock_cantidad"),
        Index("idx_mov_stock_product_id", "product_id"),
        Index("idx_mov_stock_pedido_id", "pedido_id"),
        Index("idx_mov_stock_created_at", text("created_at DESC")),
        Index("idx_mov_stock_product_tipo", "product_id", "tipo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=False,
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    cantidad: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    pedido_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pedidos.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    producto: Mapped[Producto] = relationship("Producto")  # type: ignore[name-defined]
    pedido: Mapped[Pedido | None] = relationship("Pedido")  # type: ignore[name-defined]
