"""StaffAudit model — auditoría de staff append-only (02-security.md, RN-27, M5).

Tabla inmutable: solo INSERT (nunca UPDATE/DELETE desde la aplicación).
Registra qué staff hizo qué sobre qué entidad, con estado antes/después.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base

# JSON tipado: JSONB en PostgreSQL, JSON en el resto (SQLite tests).
# Fábrica: cada columna recibe su propia instancia de tipo.
def _json_type():
    return JSON().with_variant(JSONB(astext_type=Text()), "postgresql")


class StaffAudit(Base):
    """Registro append-only de operaciones de staff (A-AUD-01)."""

    __tablename__ = "staff_audits"
    __table_args__ = (
        Index("idx_staff_audits_entidad", "entidad", "entidad_id"),
        Index("idx_staff_audits_actor", "actor_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    accion: Mapped[str] = mapped_column(String(100), nullable=False)
    entidad: Mapped[str] = mapped_column(String(50), nullable=False)
    entidad_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    datos_antes: Mapped[dict] = mapped_column(_json_type(), nullable=False, server_default=text("'{}'"), default=dict)
    datos_despues: Mapped[dict] = mapped_column(_json_type(), nullable=False, server_default=text("'{}'"), default=dict)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
