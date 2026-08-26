# Despliegue

Estrategia de contenedores y ambientes.

## Estructura del repositorio (monorepo)

| Carpeta | Proyecto | Puerto host |
| ------- | -------- | ----------- |
| `backend/` | API REST FastAPI (hot-reload: `./backend` montado en el contenedor) | 8000 |
| `frontend/` | Storefront SvelteKit (adapter-node) | 3000 |
| `admin/` | Panel SvelteKit (adapter-node) | 3001 |
| `podman-compose.yml` | Stack completo: `podman-compose up --build` | — |

El comando de arranque levanta los 4 servicios (`db`, `api`, `web`,
`admin`); la API espera a que PostgreSQL responda (`wait_for_db.py`) antes
de servir y ejecuta el bootstrap idempotente del admin (ADR-006).

Endpoints de estado:

- `GET /health` → readiness: app + conexión a base de datos + config.
- `GET /healthz` → liveness puro del proceso.

Persistencia de datos:

- **Volumen nombrado externo** (`punto_pgdata`, `external: true`): vive en
  el almacenamiento nativo de Podman y **no es eliminado** por
  `podman-compose down -v` porque no pertenece al compose. Crearlo una vez:
  `podman volume create punto_pgdata`.
- Motivo: los bind mounts desde `/mnt/*` (NTFS vía drvfs de WSL) no soportan
  `chown` POSIX → `initdb` falla con EPERM. Si el repositorio se clona en un
  filesystem Linux nativo (p. ej. `~/proyectos`), un bind mount
  `./.data/postgres:/var/lib/postgresql/data:U` vuelve a ser viable.

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
- Ventana de deduplicación de visitas configurable:
  `VISIT_DEDUP_WINDOW_HOURS` (default propuesto: `24`, RN-08/ADR-001).

## Ambientes

| Ambiente | Propósito |
| -------- | --------- |
| Desarrollo local | Podman compose local con hot reload. |
| Bootcamp/demo | Mismo compose, bootstrap de admin activo. |
| Producción | Por definir (fuera de alcance inmediato). |

## Pendientes

- CI/CD: pipeline de build y test de imágenes (herramienta por definir).
- Estrategia de migraciones de esquema (Alembic es candidato natural en FastAPI).
