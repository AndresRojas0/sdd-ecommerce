# Decisions

Registro de Decisiones de Arquitectura (ADR): decisiones importantes, su
contexto, la alternativa elegida y el motivo.

---
## Formato ADR

Cada decisión de arquitectura importante se registra como ADR numerado:

```
ADR-XXX-nombre-breve.md
```

Contenido mínimo:

| Sección | Qué contiene |
| ------- | ------------ |
| Título | Número y nombre de la decisión. |
| Contexto | Problema o situación que motivó la decisión. |
| Decisión | Qué se decidió, concreto y sin ambigüedad. |
| Alternativas | Qué se descartó y por qué. |
| Consecuencias | Impacto positivo y negativo de la decisión. |

## Consejos

- Un ADR se escribe cuando se TOMA la decisión, no después.
- Los ADR son inmutables: si la decisión cambia, se crea un ADR nuevo.

## Índice de ADRs

| ADR | Decisión |
| --- | -------- |
| ADR-001 | Conteo de visitas anónimas (cookie first-party + dedup por ventana). |
| ADR-002 | Reactivación nativa de usuarios desactivados. |
| ADR-003 | JWT en cookies + panel admin separado. |
| ADR-004 | Stack tecnológico (FastAPI / PostgreSQL / SvelteKit). |
| ADR-005 | Admin SPA consume la API por REST (superficies separadas). |
| ADR-006 | Bootstrap del admin por variables de entorno. |
| ADR-007 | Transferencia de pedidos ante vendedor de baja. |
| ADR-008 | Mecánica de descuentos (precio de oferta con vigencia). |

