# ADR-004 — Stack tecnológico del MVP

## Contexto

El proyecto necesitaba definir su stack para la tienda pública (mobile-first),
el backend y la persistencia, con contenedores reproducibles para desarrollo
y despliegue (contexto bootcamp).

## Decisión

| Capa | Tecnología |
| ---- | ---------- |
| Frontend público | **Svelte / SvelteKit** (última versión) |
| Panel de administración | **Svelte** como proyecto independiente (ver ADR-005) |
| Backend | **FastAPI** (última versión), API **REST** |
| Base de datos | **PostgreSQL** |
| Autenticación | **JWT + cookies** con refresh token obligatorio (ADR-003) |
| Sesiones/tokens | Persistencia de refresh tokens hasheados en servidor; duración tipo redes sociales (~30 días rotativos) |
| Imágenes | Dejar preparado el modelo (campo nullable, RN-13) sin implementar carga ni storage en el MVP |
| Contenedores | **Podman** con imágenes públicas de **AWS ECR Public** (`public.ecr.aws`); se evitan imágenes de Docker Hub |

## Alternativas

| Alternativa | Por qué se descarta |
| ----------- | ------------------- |
| React/Vue/Next en frontend | Elección explícita del proyecto por Svelte/SvelteKit. |
| Django/NestJS/etc. | Elección explícita del proyecto por FastAPI. |
| MySQL/MongoDB | PostgreSQL elegido por robustez relacional acorde al modelo N:M del dominio. |
| Docker / imágenes de Docker Hub | Decisión explícita: Podman + registros públicos de AWS. |
| GraphQL | REST es suficiente para el alcance actual y mantiene contratos simples. |

## Consecuencias

- Positivas: stack moderno y liviano; tipado Pydantic en backend; SSR/SSG de SvelteKit favorece SEO (slugs, RN-20); contenedores rootless con Podman.
- Negativas: ecosistema Svelte más chico que React; dos frontends (tienda + admin) que mantener; dependencia de disponibilidad de imágenes equivalentes en ECR Public.
