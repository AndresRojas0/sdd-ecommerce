"""Factura model — data-model.md §17 (RN-36, RN-37)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Factura(Base):
    """Documento fiscal 1:1 con ordenes_compra (RN-36)."""

    __tablename__ = "facturas"
    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_facturas_total"),
        Index("idx_facturas_created_at", "created_at"),
        Index("idx_facturas_created_by", "created_by"),
        Index("idx_facturas_numero_fiscal", "numero_fiscal", unique=True),
        Index("idx_facturas_orden_compra_id", "orden_compra_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    orden_compra_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ordenes_compra.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )
    numero_fiscal: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    orden_compra: Mapped[OrdenCompra] = relationship("OrdenCompra")  # type: ignore[name-defined]
    creador: Mapped[User | None] = relationship("User")  # type: ignore[name-defined]
