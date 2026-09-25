# Punto App — Backend (FastAPI)

API REST del e-commerce. Dos superficies: tienda (`/auth`, `/products`,
`/orders`, ...) y panel admin (`/admin/*`, `/admin/auth/*`), con audiencias
JWT separadas (ADR-003/005).

## Stack

FastAPI + SQLAlchemy 2 + PostgreSQL (psycopg 3), Alembic para migraciones.

## Desarrollo local

```bash
podman-compose -f podman-compose.yml up -d --build   # desde la raíz del repo
```

El servicio `api` corre `alembic upgrade head` antes de servir (compose).

## Tests

```bash
ADMIN_INITIAL_USER= ADMIN_INITIAL_PASSWORD= PYTHONPATH=backend python -m pytest -q
```

## Documentación

- Contratos de API: `docs/architecture/01-api-design.md`
- Esquema físico: `docs/domain/data-model.md`
- Decisiones: `docs/decisions/` (ADR-001..008)

## Deploy

FastAPI Cloud (`fastapi deploy` desde este directorio). Entrypoint:
`app.main:app` (`[tool.fastapi]` en `pyproject.toml`).
