"""Visita model — data-model.md §9 (RN-08, ADR-001)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Visita(Base):
    """Product visit with deduplication and origin tracking (RN-08, RN-30)."""

    __tablename__ = "visitas"
    __table_args__ = (
        CheckConstraint(
            "origen IN ('directa', 'busqueda')",
            name="ck_visitas_origen",
        ),
        CheckConstraint(
            "user_id IS NOT NULL OR visitor_cookie IS NOT NULL",
            name="ck_visitas_identificador",
        ),
        Index("idx_visitas_product_visited", "product_id", text("visited_at DESC")),
        Index("idx_visitas_user_product_time", "product_id", "user_id", "visited_at"),
        Index(
            "idx_visitas_cookie_product_time",
            "product_id",
            "visitor_cookie",
            "visited_at",
        ),
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
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    visitor_cookie: Mapped[str | None] = mapped_column(String(100), nullable=True)
    visited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    origen: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'directa'"),
        default="directa",
    )

    producto: Mapped[Producto] = relationship("Producto")  # type: ignore[name-defined]
    user: Mapped[User | None] = relationship("User")  # type: ignore[name-defined]
