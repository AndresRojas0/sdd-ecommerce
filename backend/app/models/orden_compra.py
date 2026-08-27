"""OrdenCompra model — data-model.md §15 (RN-18, RN-29)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OrdenCompra(Base):
    """Purchase order document — N pedidos → 1 OC (RN-29)."""

    __tablename__ = "ordenes_compra"
    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_ordenes_compra_total"),
        Index("idx_oc_created_at", "created_at"),
        Index("idx_oc_created_by", "created_by"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    numero: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    creador: Mapped[User | None] = relationship("User")  # type: ignore[name-defined]
    pedidos: Mapped[list[Pedido]] = relationship(  # type: ignore[name-defined]
        "Pedido", back_populates="orden_compra"
    )
