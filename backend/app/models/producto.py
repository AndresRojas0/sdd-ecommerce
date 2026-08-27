"""Producto model — data-model.md §5.

Central entity with counter caches, soft delete, GIN indexes and FK to
unidades_medida (RN-11, RN-23, RN-31, RN-32, RN-04, RN-30).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Producto(Base):
    """Product with price, visibility, soft delete and cached counters."""

    __tablename__ = "productos"
    __table_args__ = (
        CheckConstraint("precio > 0", name="ck_productos_precio"),
        CheckConstraint(
            "estado_publicacion IN ('publicado', 'oculto')",
            name="ck_productos_estado_publicacion",
        ),
        CheckConstraint("visitas_count >= 0", name="ck_productos_visitas_count"),
        CheckConstraint("guardados_count >= 0", name="ck_productos_guardados_count"),
        CheckConstraint("busquedas_count >= 0", name="ck_productos_busquedas_count"),
        CheckConstraint(
            "calificacion_promedio BETWEEN 0 AND 5",
            name="ck_productos_calificacion_promedio",
        ),
        CheckConstraint(
            "calificacion_cantidad >= 0",
            name="ck_productos_calificacion_cantidad",
        ),
        Index("idx_productos_slug", "slug", unique=True),
        Index("idx_productos_estado_publicacion", "estado_publicacion"),
        Index("idx_productos_deleted_at", "deleted_at"),
        Index("idx_productos_precio", "precio"),
        Index("idx_productos_created_at", text("created_at DESC")),
        Index(
            "idx_productos_titulo_trgm",
            "titulo",
            postgresql_using="gin",
            postgresql_ops={"titulo": "gin_trgm_ops"},
        ),
        Index(
            "idx_productos_datos_tecnicos_gin",
            "datos_tecnicos",
            postgresql_using="gin",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    componentes_incluidos: Mapped[str | None] = mapped_column(Text, nullable=True)
    datos_tecnicos: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, server_default=text("'{}'::jsonb")
    )
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    imagen: Mapped[str | None] = mapped_column(String(500), nullable=True)
    unidad_venta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("unidades_medida.id", ondelete="RESTRICT"),
        nullable=False,
    )
    estado_publicacion: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'publicado'"),
        default="publicado",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    visitas_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    guardados_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    busquedas_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    calificacion_promedio: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, server_default=text("0"), default=Decimal("0")
    )
    calificacion_cantidad: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
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

    # Relationships
    unidad_venta: Mapped[UnidadMedida] = relationship(  # type: ignore[name-defined]
        "UnidadMedida", back_populates="productos"
    )
    categorias: Mapped[list[ProductoCategoria]] = relationship(  # type: ignore[name-defined]
        "ProductoCategoria", back_populates="producto", cascade="all, delete-orphan"
    )
    etiquetas: Mapped[list[ProductoEtiqueta]] = relationship(  # type: ignore[name-defined]
        "ProductoEtiqueta", back_populates="producto", cascade="all, delete-orphan"
    )
