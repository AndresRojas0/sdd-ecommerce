# Contexto del proyecto

**Punto App** — e-commerce de ferretería con dos superficies: tienda pública
(storefront) y panel de administración separado.

## Stack

| Pieza | Tecnología | Puerto |
| ----- | ---------- | ------ |
| Backend | FastAPI + SQLAlchemy + PostgreSQL | 8000 |
| Tienda | SvelteKit con Svelte 5 (runes) | 3000 |
| Panel admin | SvelteKit (proyecto independiente) | 3001 |
| Infra | podman-compose (`db`, `api`, `web`, `admin`) | — |

## Comandos esenciales

```bash
# Levantar el stack completo
podman-compose -f podman-compose.yml up -d --build

# Tests del backend (desde la raíz del repo)
PYTHONPATH=backend pytest -q
```

## Estado actual

- Suite de tests del backend en verde.
- Flujo comercial implementado: pedidos → orden de compra (OC) → factura.
- Categorías y colecciones implementadas.

## Mapa de lectura para un agente nuevo (en orden)

1. Este archivo.
2. `docs/architecture/01-api-design.md` — contratos de la API, IDs `S-*`/`A-*`.
3. `docs/domain/data-model.md` — esquema físico de la base.
4. `docs/requirements/` — requisitos funcionales (RF), autenticación (AUTH),
   reglas de negocio (RN).
5. `docs/planning/02-open-questions.md` — qué sigue abierto.

## Convenciones clave

- La API tiene dos superficies aisladas: `/api/store` (público/comprador) y
  `/api/admin` (staff). Ver ADR-003 y ADR-005.
- Roles en `users.role`: `'comprador'`, `'vendedor'`, `'administrador'`.
  Solo vendedor y administrador operan `/api/admin`.
