"""Pedido model — data-model.md §13 (RN-26, RN-27, RN-28, RN-29)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Pedido(Base):
    """Order — lifecycle pendiente/aceptado/rechazado (RN-28)."""

    __tablename__ = "pedidos"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('pendiente', 'aceptado', 'facturado', 'en_logistica', 'entregado', 'rechazado')",
            name="ck_pedidos_estado",
        ),
        CheckConstraint(
            "motivo_rechazo IS NULL OR estado = 'rechazado'",
            name="ck_pedidos_motivo_rechazo",
        ),
        CheckConstraint("subtotal >= 0", name="ck_pedidos_subtotal"),
        CheckConstraint("total >= 0", name="ck_pedidos_total"),
        Index("idx_pedidos_user_id", "user_id"),
        Index("idx_pedidos_vendedor_id", "vendedor_id"),
        Index("idx_pedidos_estado", "estado"),
        Index("idx_pedidos_orden_compra_id", "orden_compra_id"),
        Index("idx_pedidos_created_at", text("created_at DESC")),
        Index("idx_pedidos_user_estado", "user_id", "estado"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    vendedor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    estado: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        server_default=text("'pendiente'"),
        default="pendiente",
    )
    motivo_rechazo: Mapped[str | None] = mapped_column(Text, nullable=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    orden_compra_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ordenes_compra.id", ondelete="SET NULL"),
        nullable=True,
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

    cliente: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[user_id]
    )
    vendedor: Mapped[User | None] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[vendedor_id]
    )
    orden_compra: Mapped[OrdenCompra | None] = relationship(  # type: ignore[name-defined]
        "OrdenCompra", back_populates="pedidos"
    )
    items: Mapped[list[PedidoItem]] = relationship(  # type: ignore[name-defined]
        "PedidoItem", back_populates="pedido", cascade="all, delete-orphan"
    )
