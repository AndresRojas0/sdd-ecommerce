# Flujo de trabajo

## 1. Docs-first

Toda feature nueva sigue el ciclo: delta spec (`docs/specs/TEMPLATE.md`) →
código → tests → docs actualizadas.

## 2. Ciclo SDD

El ciclo completo vive en `openspec/changes/`:
proposal → spec → design → tasks → apply → verify → archive.

## 3. Commits

- Convencionales: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`.
- Un commit por unidad de trabajo coherente.
- Tests y docs van en el mismo commit que el código que los requiere.
- Sin atribución de IA ni `Co-Authored-By`.

## 4. Endpoints

Todo endpoint nuevo o modificado se registra en
`docs/architecture/01-api-design.md` con ID `S-*` (store) o `A-*` (admin),
y se bindea a los TCs correspondientes en `docs/testing/01-test-cases.md`.

## 5. Esquema de datos

Todo cambio de esquema incluye su migración Alembic (forward-only) y
actualiza `docs/domain/data-model.md`.

## 6. Reviews y preguntas abiertas

- Hallazgos de review y su seguimiento: `docs/reviews/`, con nombre
  `<fecha>-<tema>.md` (ej. `2026-09-16-auditoria-documentacion.md`).
- Preguntas sin decidir: `docs/planning/02-open-questions.md`.
