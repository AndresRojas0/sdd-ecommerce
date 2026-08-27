"""User model — data-model.md §1.

Identity by email (RN-14), logical deactivation via is_active (RN-17),
bootstrap via env (ADR-006 / BOOT-01..04).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

ROLE_COMPRADOR = "comprador"
ROLE_VENDEDOR = "vendedor"
ROLE_ADMINISTRADOR = "administrador"


class User(Base):
    """Application user — store customer, seller or administrator."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('comprador', 'vendedor', 'administrador')",
            name="ck_users_role",
        ),
        Index("idx_users_email", "email"),
        Index("idx_users_role", "role"),
        Index("idx_users_is_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"), default=True
    )
    must_change_password: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"), default=False
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'comprador'"),
        default=ROLE_COMPRADOR,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
