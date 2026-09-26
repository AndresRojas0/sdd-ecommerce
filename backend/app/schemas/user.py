"""User schemas — UC-C06/07/09/10, RF-28; user lifecycle via panel A-USR-07..09."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UpdateMeRequest(BaseModel):
    display_name: str

    model_config = {"extra": "forbid"}


class UpdateAvatarRequest(BaseModel):
    avatar: str

    model_config = {"extra": "forbid"}


class AdminUserProfileUpdate(BaseModel):
    """A-USR-03: edición acotada de perfil por staff.

    `extra=forbid` rechaza con 422 cualquier campo no listado —
    en particular `role` y `password` nunca son editables aquí.
    """

    display_name: str | None = None
    avatar: str | None = None

    model_config = {"extra": "forbid"}


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    avatar: str | None
    role: str
    is_active: bool
    must_change_password: bool
    created_at: datetime
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# A-USR-07/08/09 — user lifecycle from the panel
# ---------------------------------------------------------------------------

# The panel never creates or promotes administrators: bootstrap via env
# (BOOT-01/02, ADR-006) is the only path to the `administrador` role.
PANEL_ASSIGNABLE_ROLES = ("comprador", "vendedor")


def _validate_panel_role(value: str) -> str:
    if value not in PANEL_ASSIGNABLE_ROLES:
        raise ValueError("role debe ser 'comprador' o 'vendedor' (el panel no crea ni asigna administradores)")
    return value


class UserCreateRequest(BaseModel):
    """A-USR-07: alta de usuario desde el panel (rol acotado, sin administradores)."""

    email: EmailStr
    display_name: str
    role: str
    temp_password: str | None = None

    model_config = {"extra": "forbid"}

    @field_validator("display_name")
    @classmethod
    def validate_display(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError("display_name requerido")
        if len(v.strip()) > 100:
            raise ValueError("display_name máximo 100")
        return v.strip()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        return _validate_panel_role(v)


class PasswordResetRequest(BaseModel):
    """A-USR-08: `temp_password` opcional; si falta, el backend genera una."""

    temp_password: str | None = None

    model_config = {"extra": "forbid"}


class RoleChangeRequest(BaseModel):
    """A-USR-09: cambio de rol acotado a comprador/vendedor (sin auto-promoción)."""

    role: str

    model_config = {"extra": "forbid"}

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        return _validate_panel_role(v)


class AdminUserCreateResponse(BaseModel):
    """A-USR-07: `temp_password` viaja UNA sola vez en esta respuesta."""

    user: AdminUserResponse
    temp_password: str
    aviso: str


class PasswordResetResponse(BaseModel):
    """A-USR-08: respuesta mínima — la contraseña temporal solo vive aquí."""

    temp_password: str
    aviso: str
