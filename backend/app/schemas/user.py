"""User schemas — UC-C06/07/09/10, RF-28."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class UpdateMeRequest(BaseModel):
    display_name: str

    model_config = {"extra": "forbid"}


class UpdateAvatarRequest(BaseModel):
    avatar: str

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
