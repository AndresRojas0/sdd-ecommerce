# Despliegue

Estrategia de contenedores y ambientes (primera iteración).

## Contenedores (Podman)

Todos los servicios corren en **Podman**. Las imágenes base provienen de
**AWS ECR Public** (`public.ecr.aws`); se evitan imágenes de Docker Hub.

| Servicio | Imagen base (ECR Public) | Nota |
| -------- | ------------------------ | ---- |
| Storefront (SvelteKit) | `public.ecr.aws/docker/library/node` | Build + runtime Node. |
| Admin SPA | `public.ecr.aws/docker/library/node` | Build estático servido por nginx o Node. |
| Backend FastAPI | `public.ecr.aws/docker/library/python` | Uvicorn como servidor ASGI. |
| PostgreSQL | `public.ecr.aws/docker/library/postgres` | Volumen nombrado para datos. |

> Verificar la disponibilidad de cada tag en `public.ecr.aws` antes de
> fijar versiones; el espejo de Docker Library en ECR Public mantiene las
> imágenes oficiales.

## Configuración por entorno

Variables de entorno del backend (sin secretos en el repo):

- Conexión a PostgreSQL (`DATABASE_URL`).
- Secretos JWT separados por audiencia (`JWT_SECRET_STORE`,
  `JWT_SECRET_ADMIN`) y parámetros de expiración.
- Bootstrap de admin: `ADMIN_INITIAL_EMAIL`, `ADMIN_INITIAL_PASSWORD`,
  `ADMIN_INITIAL_DISPLAY_NAME` (solo primer arranque, ADR-006).

## Ambientes

| Ambiente | Propósito |
| -------- | --------- |
| Desarrollo local | Podman compose local con hot reload. |
| Bootcamp/demo | Mismo compose, bootstrap de admin activo. |
| Producción | Por definir (fuera de alcance inmediato). |

## Pendientes

- CI/CD: pipeline de build y test de imágenes (herramienta por definir).
- Estrategia de migraciones de esquema (Alembic es candidato natural en FastAPI).
