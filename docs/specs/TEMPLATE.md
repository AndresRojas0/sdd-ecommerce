# Plantilla de delta spec

Copiar este archivo a `specs/<nombre-del-cambio>.md` y completar.

---

# Spec: <nombre del cambio>

- **Change ID**: `<nombre-del-cambio>`
- **Estado**: propuesta | aprobada | implementada | archivada

## Contexto

<1-2 líneas: problema u oportunidad que motiva el cambio.>

## Requisitos

Requisitos numerados, con fortaleza RFC 2119 (MUST / SHOULD / MAY) y
referencias a RF-xx / RN-xx / UC-xx / endpoints S-* o A-*.

| # | Requisito | Fortaleza | Refs |
| - | --------- | --------- | ---- |
| R1 | <requisito verificable> | MUST | RF-xx, RN-xx |
| R2 | <requisito verificable> | SHOULD | A-XX-NN |

## Escenarios

Formato Given/When/Then; un escenario por cada requisito crítico.

### E1 — <título>

- **Given** <estado inicial>
- **When** <acción>
- **Then** <resultado observable>

## Impacto

- **Endpoints**: nuevos <S-*/A-*>; modificados <...>.
- **Esquema + migración**: tablas/columnas afectadas; revisión Alembic
  `<revision>` (forward-only, sin editar revisiones ya aplicadas).
- **Docs a actualizar**: <lista de documentos afectados>.

## Criterios de verificación

| Criterio | TC | Estado |
| -------- | -- | ------ |
| <verificación> | TC-xx existente / nuevo | pendiente |
