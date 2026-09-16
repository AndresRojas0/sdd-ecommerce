# Domain

Define los conceptos principales del negocio: entidades, relaciones y la
información que representa cada una.

---
## Documentos esperados

| Archivo | Qué contiene |
| ------- | ------------ |
| `domain-model.md` | Modelo conceptual del sistema: conceptos y relaciones. |
| `data-model.md` | Esquema físico: DDL PostgreSQL completo con CHECKs, índices y extensiones (§22). |

> `domain-model.md` y `data-model.md`: existentes. `entities.md`: retirado — su contenido quedó absorbido por `data-model.md`.

## Consejos

- El modelo de dominio debe entenderse sin leer código.
- Cuando cambia una entidad, actualizá el dominio ANTES del schema.

