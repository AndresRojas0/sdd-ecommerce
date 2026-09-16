# Estándares de código

Resumen por capa. Verificar contra el código real al editarlo: este doc
resume, no reemplaza el estilo existente.

## Backend (FastAPI)

- Routers separados por superficie: `/api/store` vs `/api/admin`.
- Reglas de negocio (RN) en la capa de servicios, nunca en los routers.
- Pydantic para request/response.
- SQLAlchemy con sesiones por request.
- Errores con el envelope de `docs/architecture/01-api-design.md`:
  `409` para conflicto de estado/stock, `422` para validación de negocio.
- Snapshots de precios al momento de la operación (nunca recalcular a
  posteriori).

## Frontend (SvelteKit + Svelte 5)

- Runes: `$state`, `$derived`, `$props`, `$effect`.
- Componentes en `src/lib/components`; stores en `src/lib/stores`.
- Estilos con Tailwind utilities tomando los colores de los tokens CSS del
  design system vía valores arbitrarios (`bg-[var(--blue)]`,
  `text-[var(--yellow)]` — ver `docs/ui/03-design-system.md`); no hex
  hardcodeados.

## General

- Identificadores y código en inglés; los comentarios de dominio pueden ir
  en español neutro.
- Sin lógica de negocio en componentes de UI.
- Idempotencia y deduplicación server-side: nunca confiar en el cliente.

## Tests

- pytest con `PYTHONPATH=backend` (desde la raíz).
- El nombre del test alinea al TC que cubre, cuando existe.
