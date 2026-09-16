# Auditoría de documentación — 2026-09-16

Primera revisión real del proyecto: auditoría de los 47 documentos.

## Alcance

Árbol `docs/` (visión, requisitos, dominio, use-cases, architecture, UI,
testing, planning, specs, reviews) más el store SDD en `openspec/`.

## Hallazgos

1. **Capa de spec sólida y cross-referenciada**: RF/RN/UC enlazados con
   endpoints y TCs en ambas direcciones.
2. **Capa de proceso andamio**: `planning/`, `specs/` y `reviews/` tenían
   solo READMEs que declaraban documentos "planeados, aún no creados".
3. **API design pendiente = bloqueante de TCs**: sin diseño de endpoints
   no había binding verificable de los casos de prueba.
4. **Docs stale**: `domain/README.md`, ADR-003 línea 49, índices de
   `use-cases/` y de `decisions/`.
5. **Sin glosario de dominio dedicado** (parcialmente cubierto por
   `.ai/glossary.md`).

## Acciones

| Acción | Estado |
| ------ | ------ |
| Diseño de API + binding de TCs | Hecha (`8ab671f`) |
| Decisiones abiertas: ADR-008, rate limiting, auditoría de staff, CI/CD, migraciones, producción | Hechas (`f83a167`) |
| Materializar carpetas andamio (planning/specs/reviews) | Hecha (este change) |
| Inconsistencias stale: READMEs de domain/vision/requirements, índice de ADRs en `decisions/README.md` | Pendiente |
| Glosario de dominio (parcialmente cubierto por `.ai/glossary.md`) | Pendiente |
| Diferidos: pagos, envíos, recovery, imágenes | Por diseño — no requieren acción |

## Seguimiento

Los ítems abiertos se trackean en `planning/02-open-questions.md`.
