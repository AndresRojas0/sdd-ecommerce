"""Alembic env — wires target_metadata from SQLAlchemy Base.

Loads DATABASE_URL from settings so ``alembic.ini`` placeholder is
overridden at runtime. Imports all models so Base.metadata is complete.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.db.base import Base

# Import all models for metadata completeness (side-effect).
import app.models  # noqa: F401  # pylint: disable=unused-import

# Import may run outside Alembic (e.g. py_compile / unit tests); guard accordingly.
try:
    config = context.config  # type: ignore[attr-defined]
except AttributeError:
    config = None  # type: ignore[assignment]

if config is not None and config.config_file_name is not None:
    fileConfig(config.config_file_name)

if config is not None:
    try:
        settings = get_settings()
        config.set_main_option("sqlalchemy.url", settings.database_url)
    except Exception:  # pragma: no cover — env import without DB
        pass

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if config is not None:
    try:
        if context.is_offline_mode():
            run_migrations_offline()
        else:
            run_migrations_online()
    except Exception:
        # Not running inside Alembic context (proxy not established) — import-safe
        pass
