"""Admin bootstrap (ADR-006).

On startup, if no administrator exists and ADMIN_INITIAL_* is configured,
create the initial admin with must_change_password=True. Idempotent:
any pre-existing admin short-circuits the seed (BOOT-01).

Schema management is via Alembic. In production ``alembic upgrade head``
runs before this bootstrap (e.g. container entrypoint). For dev
convenience this module falls back to ``Base.metadata.create_all`` when
tables are missing so the bootstrap does not crash on a fresh volume
before the first migration.
"""

import logging

from sqlalchemy import inspect, select, text

from app.core.config import get_settings
from app.core.security import PasswordPolicyError, hash_password, validate_policy
from app.db.base import Base, SessionLocal, engine
from app.models.user import ROLE_ADMINISTRADOR, User

logger = logging.getLogger("bootstrap")


def _ensure_tables() -> None:
    """Fallback: create tables via metadata if Alembic has not yet run.

    Checks whether the ``users`` table exists; if not, invokes
    ``Base.metadata.create_all``. This is a dev-only convenience — in
    production Alembic is the source of truth and this path is no-op.
    """
    try:
        # Ensure all models are imported so Base.metadata is populated
        # (Base itself does not import models to avoid circular imports).
        import app.models  # noqa: F401  # side-effect: registers tables

        inspector = inspect(engine)
        if not inspector.has_table("users"):
            logger.info(
                "Tablas no encontradas: ejecutando Base.metadata.create_all como fallback "
                "(en producción usar 'alembic upgrade head')."
            )
            # Ensure pgcrypto extension exists so gen_random_uuid() default works
            # even when create_all is used without migration.
            with engine.begin() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            Base.metadata.create_all(bind=engine)
    except Exception as exc:  # noqa: BLE001
        # Non-fatal: bootstrap will fail on next query and surface the error.
        logger.warning("No se pudo verificar/crear tablas fallback: %s", exc)


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

    _ensure_tables()

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
