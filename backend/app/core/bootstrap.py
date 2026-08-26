"""Admin bootstrap (ADR-006).

On startup, if no administrator exists and ADMIN_INITIAL_* is configured,
create the initial admin with must_change_password=True. Idempotent:
any pre-existing admin short-circuits the seed (BOOT-01).
"""

import logging

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import PasswordPolicyError, hash_password, validate_policy
from app.db.base import SessionLocal
from app.models.user import ROLE_ADMINISTRADOR, User

logger = logging.getLogger("bootstrap")


def run_bootstrap() -> None:
    settings = get_settings()

    if not settings.admin_initial_user or not settings.admin_initial_password:
        logger.info("ADMIN_INITIAL_* no configurado: bootstrap omitido (BOOT-01).")
        return

    try:
        validate_policy(settings.admin_initial_password)
    except PasswordPolicyError as exc:
        # BOOT-02: fallar ruidoso es preferible a sembrar credenciales débiles.
        raise RuntimeError(f"Bootstrap abortado: {exc}") from exc

    with SessionLocal() as db:
        existing_admin = db.scalar(
            select(User).where(User.role == ROLE_ADMINISTRADOR).limit(1)
        )
        if existing_admin is not None:
            logger.info("Ya existe un administrador: bootstrap omitido (BOOT-01).")
            return

        taken = db.scalar(select(User).where(User.email == settings.admin_initial_user))
        email = (
            settings.admin_initial_user
            if taken is None
            else f"{settings.admin_initial_user}.admin"
        )

        admin = User(
            email=email,
            display_name=settings.admin_initial_display_name or "Administrador",
            password_hash=hash_password(settings.admin_initial_password),
            role=ROLE_ADMINISTRADOR,
            is_active=True,
            must_change_password=True,  # BOOT-03: cambio forzado en el primer login.
        )
        db.add(admin)
        db.commit()
        logger.info("Administrador inicial creado para %s (BOOT-03 activo).", email)
