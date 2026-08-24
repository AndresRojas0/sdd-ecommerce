# Use Cases

Define las interacciones entre los actores y el sistema para lograr un
objetivo concreto.

---
## Índice de casos de uso

| Archivo | Actor | Estado |
| ------- | ----- | ------ |
| `visitante-anonimo.md` | Visitante anónimo | Especificado (UC-A01..A10) |
| `cuenta.md` | Comprador y Vendedor (autogestión) | Especificado (UC-C01..C10; UC-C04 diferido por AUTH-06) |
| `comprador.md` | Comprador | Especificado (UC-B01..B10) |
| `vendedor.md` | Vendedor | Especificado (UC-V01..V09); superficie por confirmar |
| `administrador.md` | Administrador | Reservado: se define en el proyecto del panel admin |

## Convenciones

- Un archivo por actor o grupo de casos relacionados, con actor,
  precondición, flujo principal y flujos alternativos.
- IDs estables (`UC-<actor><n>`) para trazabilidad con `docs/testing/`.

## Consejos

- Un caso de uso debe ser accionable: el lector entiende qué hace el sistema.
- Los casos de uso alimentan los casos de prueba de `docs/testing/`.

