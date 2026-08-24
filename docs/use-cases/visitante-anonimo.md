# Casos de uso — Visitante anónimo

Actor no autenticado sobre la tienda pública. El catálogo es público
(RN-10): todo lo de este documento no requiere sesión.

| ID | Caso de uso |
| -- | ----------- |
| UC-A01 | Ingresar a la aplicación y ver productos |
| UC-A02 | Buscar productos por nombre |
| UC-A03 | Buscar productos por componente (componentes incluidos / datos técnicos) |
| UC-A04 | Filtrar por categorías |
| UC-A05 | Filtrar por tags (con autocompletado mientras escribe, RN-03) |
| UC-A06 | Combinar todos los filtros y búsquedas en una sola consulta (RN-04/RN-05) |
| UC-A07 | Ordenar resultados (relevancia, más reciente, con descuento, precio ↑↓, A-Z, Z-A — RN-07) |
| UC-A08 | Ver detalle de un producto (genera una visita, RN-08/ADR-001) |
| UC-A09 | Compartir producto (enlace público con slug, RF-22) |

## Flujos alternativos transversales

- **UC-A10 — Intento de acción que requiere autenticación**: si el visitante
  intenta favoritar, armar carrito, pedir o calificar, el sistema lo redirige
  a iniciar sesión (o registrarse) y conserva el contexto para continuar
  después de autenticarse.
