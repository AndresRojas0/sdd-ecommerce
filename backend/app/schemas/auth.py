"""Auth schemas — RN-14, RN-15, AUTH-05."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.core.security import POLICY


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str
    password: str
    avatar: str | None = None

    @field_validator("display_name")
    @classmethod
    def validate_display(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError("display_name requerido")
        if len(v) > 100:
            raise ValueError("display_name máximo 100")
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_pwd(cls, v: str) -> str:
        import re

        if not POLICY.search(v):
            raise ValueError(
                "La contraseña debe tener mínimo 8 caracteres, una mayúscula, un número y un caracter especial."
            )
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new(cls, v: str) -> str:
        if not POLICY.search(v):
            raise ValueError(
                "La contraseña debe tener mínimo 8 caracteres, una mayúscula, un número y un caracter especial."
            )
        return v


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    avatar: str | None = None
    role: str
    is_active: bool
    must_change_password: bool
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = {"from_attributes": True}


class ReactivateRequest(BaseModel):
    email: EmailStr
    password: str
