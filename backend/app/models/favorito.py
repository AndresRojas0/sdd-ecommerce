"""Favorito model — data-model.md §8 (RN-09)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Favorito(Base):
    """Saved product — increments productos.guardados_count."""

    __tablename__ = "favoritos"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_favoritos_user_product"),
        Index("idx_favoritos_user_id", "user_id"),
        Index("idx_favoritos_product_id", "product_id"),
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    user: Mapped[User] = relationship("User")  # type: ignore[name-defined]
    producto: Mapped[Producto] = relationship("Producto")  # type: ignore[name-defined]
