"""Categoria model — data-model.md §2 (RN-01, RN-38, RN-20)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, SmallInteger, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base


class Categoria(Base):
    """Closed taxonomy category — tree 2 levels (RN-01, RN-38)."""

    __tablename__ = "categorias"
    __table_args__ = (
        CheckConstraint(
            "color ~ '^#[0-9A-Fa-f]{6}$'",
            name="ck_categorias_color",
        ),
        CheckConstraint(
            "nivel IN (1, 2)",
            name="ck_categorias_nivel",
        ),
        CheckConstraint(
            "(parent_id IS NULL AND nivel = 1) OR (parent_id IS NOT NULL AND nivel = 2)",
            name="ck_categorias_nivel_parent",
        ),
        Index("idx_categorias_slug", "slug", unique=True),
        Index("idx_categorias_parent_id", "parent_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categorias.id", ondelete="RESTRICT"),
        nullable=True,
        default=None,
    )
    nivel: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        server_default=text("1"),
        default=1,
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

    # Self-referential tree (RESTRICT on delete, no orphan cascade)
    parent: Mapped[Categoria | None] = relationship(
        "Categoria",
        remote_side=[id],
        back_populates="children",
        foreign_keys=[parent_id],
    )
    children: Mapped[list[Categoria]] = relationship(
        "Categoria",
        back_populates="parent",
        foreign_keys=[parent_id],
    )

    # Relationships (optional, for ORM convenience)
    productos: Mapped[list[ProductoCategoria]] = relationship(  # type: ignore[name-defined]
        "ProductoCategoria", back_populates="categoria", cascade="all, delete-orphan"
    )

    @validates("nivel")
    def validate_nivel(self, key: str, value: int) -> int:
        if value not in (1, 2):
            raise ValueError("nivel debe ser 1 o 2")
        return value
