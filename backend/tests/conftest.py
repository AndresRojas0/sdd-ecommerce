"""Test fixtures — PostgreSQL if available else SQLite fallback (TEST-03).

Per testing/00-strategy.md tests should use PostgreSQL real, but CI/local
without DB must still run: fallback to SQLite in-memory.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base, get_db
from app.main import app as fastapi_app
from app.models.categoria import Categoria
from app.models.etiqueta import Etiqueta
from app.models.producto import Producto
from app.models.unidad_medida import UnidadMedida
from app.models.user import User

# Import all models to populate Base
import app.models as _app_models  # noqa: F401

TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    # Try PostgreSQL via DATABASE_URL if reachable, else SQLite
    settings = get_settings()
    # Force SQLite for portability unless TEST_DATABASE_URL explicitly set
    import os

    url = os.getenv("TEST_DATABASE_URL")
    if url:
        try:
            eng = create_engine(url, pool_pre_ping=True)
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            # create
            Base.metadata.create_all(bind=eng)
            # seed extensions not needed
            yield eng
            eng.dispose()
            return
        except Exception:
            pass
    # SQLite fallback
    eng = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite needs to enable foreign keys
    @event.listens_for(eng, "connect")
    def _fk_on(dbapi_conn, conn_rec):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Sanitize metadata for SQLite: remove PG-specific constructs
    def _sanitize_for_sqlite():
        from sqlalchemy import JSON, CheckConstraint, Text
        from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB, UUID as PG_UUID

        for table in list(Base.metadata.tables.values()):
            to_remove = [idx for idx in table.indexes if idx.dialect_options.get("postgresql", {}).get("using") == "gin"]
            for idx in to_remove:
                table.indexes.discard(idx)
            to_remove_cc = []
            for c in table.constraints:
                if isinstance(c, CheckConstraint):
                    sql = str(c.sqltext)
                    if "~" in sql:
                        to_remove_cc.append(c)
            for cc in to_remove_cc:
                table.constraints.discard(cc)
            for col in table.columns:
                # JSONB -> JSON (SQLite compatible)
                if isinstance(col.type, PG_JSONB):
                    col.type = JSON()
                # UUID handling already via PG_UUID -> keep but server_default removed below
                if col.server_default is not None:
                    arg = str(col.server_default.arg) if hasattr(col.server_default, "arg") else str(col.server_default)
                    if "gen_random_uuid" in arg or "now()" in arg or "'{}'::jsonb" in arg or "'comprador'" in arg or "'publicado'" in arg or "'pendiente'" in arg or "'directa'" in arg:
                        col.server_default = None
                    elif arg.strip() in ("true", "false", "'true'", "'false'", "0"):
                        if col.name in ("visitas_count", "guardados_count", "busquedas_count", "calificacion_cantidad", "cantidad_disponible", "cantidad_reservada"):
                            col.server_default = None
                        elif col.name in ("is_active", "must_change_password", "revoked"):
                            col.server_default = None
                        elif col.name in ("total", "subtotal", "precio", "precio_unitario"):
                            col.server_default = None

    _sanitize_for_sqlite()
    # Auto-generate UUIDs and timestamps for SQLite
    from sqlalchemy.orm import Session as SASession

    @event.listens_for(SASession, "before_flush")
    def _generate_defaults(session, flush_context, instances):
        for obj in session.new:
            if hasattr(obj, "id") and getattr(obj, "id", None) is None:
                # Only for tables with UUID PK named id
                try:
                    obj.id = uuid.uuid4()
                except Exception:
                    pass
            # timestamps
            now = datetime.now(timezone.utc)
            for attr in ("created_at", "updated_at", "visited_at", "expires_at"):
                if hasattr(obj, attr) and getattr(obj, attr, None) is None:
                    # set only if column exists and is not nullable? covers most
                    if attr == "expires_at":
                        continue  # handled by business logic
                    setattr(obj, attr, now)
            # defaults for counters/strings
            if hasattr(obj, "visitas_count") and getattr(obj, "visitas_count", None) is None:
                obj.visitas_count = 0
            if hasattr(obj, "guardados_count") and getattr(obj, "guardados_count", None) is None:
                obj.guardados_count = 0
            if hasattr(obj, "busquedas_count") and getattr(obj, "busquedas_count", None) is None:
                obj.busquedas_count = 0
            if hasattr(obj, "calificacion_cantidad") and getattr(obj, "calificacion_cantidad", None) is None:
                obj.calificacion_cantidad = 0
            if hasattr(obj, "calificacion_promedio") and getattr(obj, "calificacion_promedio", None) is None:
                from decimal import Decimal
                obj.calificacion_promedio = Decimal("0")
            if hasattr(obj, "is_active") and getattr(obj, "is_active", None) is None:
                obj.is_active = True
            if hasattr(obj, "must_change_password") and getattr(obj, "must_change_password", None) is None:
                obj.must_change_password = False
            if hasattr(obj, "revoked") and getattr(obj, "revoked", None) is None:
                obj.revoked = False
            if hasattr(obj, "role") and getattr(obj, "role", None) is None:
                obj.role = "comprador"
            if hasattr(obj, "estado_publicacion") and getattr(obj, "estado_publicacion", None) is None:
                obj.estado_publicacion = "publicado"
            if hasattr(obj, "estado") and getattr(obj, "estado", None) is None:
                obj.estado = "pendiente"
            if hasattr(obj, "origen") and getattr(obj, "origen", None) is None:
                obj.origen = "directa"
            if hasattr(obj, "datos_tecnicos") and getattr(obj, "datos_tecnicos", None) is None:
                obj.datos_tecnicos = {}
            # stock defaults
            if hasattr(obj, "cantidad_disponible") and getattr(obj, "cantidad_disponible", None) is None:
                from decimal import Decimal
                obj.cantidad_disponible = Decimal("0")
            if hasattr(obj, "cantidad_reservada") and getattr(obj, "cantidad_reservada", None) is None:
                from decimal import Decimal
                obj.cantidad_reservada = Decimal("0")
            if hasattr(obj, "cantidad") and getattr(obj, "cantidad", None) is None:
                pass
            if hasattr(obj, "tipo") and getattr(obj, "tipo", None) is None:
                pass
            # ensure updated_at for Stock
            if hasattr(obj, "updated_at") and getattr(obj, "updated_at", None) is None:
                obj.updated_at = now
            # ensure product_id for Stock PK fallback (handled by caller)

    Base.metadata.create_all(bind=eng)
    # Seed minimal required data (unidades, categorias)
    Session = sessionmaker(bind=eng)
    with Session() as s:
        # Use deterministic ids for seeds
        um = s.query(UnidadMedida).first()
        if not um:
            s.add_all(
                [
                    UnidadMedida(nombre="unidades", simbolo="u"),
                    UnidadMedida(nombre="cm", simbolo="cm"),
                    UnidadMedida(nombre="m", simbolo="m"),
                    UnidadMedida(nombre="kg", simbolo="kg"),
                ]
            )
            s.commit()
        if not s.query(Categoria).first():
            s.add(Categoria(nombre="herramientas", slug="herramientas", color="#6B4226"))
            s.add(Categoria(nombre="electricidad", slug="electricidad", color="#FFCC00"))
            s.commit()
        if not s.query(Etiqueta).first():
            s.add(Etiqueta(nombre="acero", slug="acero"))
            s.add(Etiqueta(nombre="tornillos", slug="tornillos"))
            s.commit()
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture
def db_session(engine):
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = SessionLocal()
    # Start nested transaction
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(db_session):
    def _override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def comprador(db_session):
    user = User(
        email=f"comprador_{uuid.uuid4().hex[:6]}@test.com",
        display_name="Comprador",
        password_hash=hash_password("Abcdef1!"),
        role="comprador",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def vendedor(db_session):
    user = User(
        email=f"vendedor_{uuid.uuid4().hex[:6]}@test.com",
        display_name="Vendedor",
        password_hash=hash_password("Abcdef1!"),
        role="vendedor",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin(db_session):
    user = User(
        email=f"admin_{uuid.uuid4().hex[:6]}@test.com",
        display_name="Admin",
        password_hash=hash_password("Abcdef1!"),
        role="administrador",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_header(client: TestClient, email: str, password: str = "Abcdef1!") -> dict:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    # Extract access_token cookie
    token = resp.cookies.get("access_token") or resp.cookies.get("access_token")
    if token:
        return {"Cookie": f"access_token={token}"}
    # Fallback try header
    return {}


def auth_client_for(client: TestClient, user: User) -> dict:
    return auth_header(client, user.email)


@pytest.fixture
def unidad(db_session):
    um = db_session.query(UnidadMedida).filter_by(nombre="unidades").first()
    return um


@pytest.fixture
def categoria(db_session):
    cat = db_session.query(Categoria).filter_by(slug="herramientas").first()
    return cat


@pytest.fixture
def etiqueta(db_session):
    tag = db_session.query(Etiqueta).filter_by(slug="acero").first()
    return tag


def create_product_fixture(client, categoria, unidad, vendedor, etiqueta=None, slug_suffix: str | None = None):
    sfx = slug_suffix or uuid.uuid4().hex[:6]
    headers = auth_client_for(client, vendedor)
    payload = {
        "titulo": f"Producto {sfx}",
        "slug": f"producto-{sfx}",
        "descripcion": "desc",
        "precio": "10.50",
        "unidad_venta_id": str(unidad.id),
        "categoria_ids": [str(categoria.id)],
        "etiqueta_ids": [str(etiqueta.id)] if etiqueta else [],
    }
    resp = client.post("/products", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()
