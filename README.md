# Punto App

Ecommerce de ferretería desarrollado con Specification-Driven Development.
Toda la especificación vive en [`docs/`](docs/README.md) — leela antes de
tocar código.

## Estructura del repositorio

| Carpeta | Proyecto | Puerto |
| ------- | -------- | ------ |
| `backend/` | API REST FastAPI | 8000 |
| `frontend/` | Storefront SvelteKit (mobile-first) | 3000 |
| `admin/` | Panel de administración SvelteKit (login propio, ADR-005) | 3001 |
| `docs/` | Especificación SDD: fuente de verdad del proyecto | — |

## Levantar el stack completo

Requiere [Podman](https://podman.io/).

```bash
cp .env.example .env   # completar secretos antes del primer arranque
podman-compose up --build
```

| URL | Servicio |
| --- | -------- |
| http://localhost:3000 | Storefront |
| http://localhost:3001 | Admin |
| http://localhost:8000/health | Estado de la API + conexión a DB |

## Regla del proyecto

Primero documentación, después implementación, después pruebas:
si el comportamiento cambia, se actualiza la spec ANTES que el código.
