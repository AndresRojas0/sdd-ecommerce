"""Stock model — data-model.md §16.1 (RN-35)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Stock(Base):
    """Stock por producto — 1:1 con productos (RN-35)."""

    __tablename__ = "stock"
    __table_args__ = (
        CheckConstraint("cantidad_disponible >= 0", name="ck_stock_disponible"),
        CheckConstraint("cantidad_reservada >= 0", name="ck_stock_reservada"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="CASCADE"),
        primary_key=True,
    )
    cantidad_disponible: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, server_default=text("0"), default=Decimal("0")
    )
    cantidad_reservada: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, server_default=text("0"), default=Decimal("0")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    producto: Mapped[Producto] = relationship("Producto")  # type: ignore[name-defined]
