# Specs

Especificaciones SDD. Cada cambio del proyecto tiene su propia
especificación (delta spec) con requisitos y escenarios.

---
## Estructura SDD

Cada cambio del proyecto sigue el ciclo SDD:

```
proposal → spec → design → tasks → apply → verify → archive
```

En esta carpeta se guardan las especificaciones (delta specs) con formato:

```
specs/<nombre-del-cambio>.md
```

Los changes activos viven en `openspec/changes/` (store SDD); esta carpeta
guarda la guía, la plantilla y el índice de specs archivadas.

Cada spec contiene requisitos con su fortaleza (MUST / SHALL / SHOULD) y
escenarios verificables.

## Documentos esperados

| Archivo | Qué contiene |
| ------- | ------------ |
| `README.md` | Este índice y guía del ciclo SDD. |
| `TEMPLATE.md` | Plantilla para escribir una spec nueva. |

> `TEMPLATE.md`: creado (2026-09-16); `<cambio>.md` se agrega con cada change.
| `<cambio>.md` | Spec de un cambio concreto (se agrega con cada change). |

## Consejos

- La spec se escribe ANTES del código: es el contrato del cambio.
- Si un requisito no se puede verificar, no es un requisito.

