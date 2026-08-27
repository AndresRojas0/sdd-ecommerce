"""Calificacion model — data-model.md §10 (RN-21, RN-33)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, SmallInteger, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Calificacion(Base):
    """One rating per user/product, editable (RN-21)."""

    __tablename__ = "calificaciones"
    __table_args__ = (
        CheckConstraint(
            "estrellas BETWEEN 1 AND 5",
            name="ck_calificaciones_estrellas",
        ),
        UniqueConstraint("user_id", "product_id", name="uq_calificaciones_user_product"),
        Index("idx_calificaciones_product_id", "product_id"),
        Index("idx_calificaciones_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=False,
    )
    estrellas: Mapped[int] = mapped_column(SmallInteger, nullable=False)
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

    user: Mapped[User] = relationship("User")  # type: ignore[name-defined]
    producto: Mapped[Producto] = relationship("Producto")  # type: ignore[name-defined]
