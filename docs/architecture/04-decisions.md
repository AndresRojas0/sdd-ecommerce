# Índice de decisiones técnicas

Registro de las decisiones técnicas del proyecto. El detalle completo y su
racional vive en `docs/decisions/` como ADR numerado.

| ADR | Decisión | Estado |
| --- | -------- | ------ |
| [ADR-001](../decisions/ADR-001-conteo-visitas-anonimas.md) | Conteo de visitas con usuarios anónimos (cookie UUID + ventana de deduplicación) | Aceptada; ventana **configurable** por entorno (RN-08), default 24 h |
| [ADR-002](../decisions/ADR-002-reactivacion-nativa-usuarios.md) | Reactivación nativa del usuario dado de baja | Aceptada |
| [ADR-003](../decisions/ADR-003-jwt-cookies-y-admin-separado.md) | JWT en cookies (access 15 min, refresh rotativo 30 días) | Aceptada; acceso del admin a datos superseded por ADR-005 |
| [ADR-004](../decisions/ADR-004-stack-tecnologico.md) | Stack: SvelteKit + FastAPI + PostgreSQL + REST + Podman/ECR Public | Aceptada |
| [ADR-005](../decisions/ADR-005-admin-spa-consume-api.md) | Admin como SPA Svelte independiente que consume la API REST | Aceptada |
| [ADR-006](../decisions/ADR-006-bootstrap-admin-por-env.md) | Bootstrap de admin por variables de entorno con cambio forzado | Aceptada |
| [ADR-007](../decisions/ADR-007-transferencia-pedidos-vendedor-de-baja.md) | Baja de Vendedor: OC congeladas, pedidos pendientes reasignables por Admin | Aceptada |

## Decisiones pendientes de ADR

- Algoritmo de "relevancia" para ordenamiento de búsqueda.
- Mecánica de descuentos (% vs. precio final, vigencia).
