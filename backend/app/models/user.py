"""ORM models.

PROVISIONAL: the User model here is the minimum needed by the admin
bootstrap (ADR-006). The definitive schema comes from the physical data
model (domain/data-model.md) and will be managed by Alembic migrations;
this create_all-based table must not accumulate business columns.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

ROLE_COMPRADOR = "comprador"
ROLE_VENDEDOR = "vendedor"
ROLE_ADMINISTRADOR = "administrador"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)  # null en MVP (RN-13 análogo)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Baja lógica (RN-17): nunca DELETE físico.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Bootstrap ADR-006: fuerza el cambio de contraseña en el primer login.
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # PROVISIONAL: columna simple hasta que exista la tabla de roles.
    role: Mapped[str] = mapped_column(String(20), default=ROLE_COMPRADOR, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
