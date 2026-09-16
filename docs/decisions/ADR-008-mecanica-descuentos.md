# ADR-008 — Mecánica de descuentos (precio de oferta con vigencia)

**Estado**: Aceptada.

## Contexto

RN-07 lista el ordenamiento "con descuento" entre los ordenamientos
soportados del catálogo, y `scope.md` lo declara in-scope pero con la
mecánica sin definir ("falta definir mecánica"). El modelo de datos
reserva `pedidos.total` (hoy igual al subtotal) y sugiere como opciones
futuras una columna `productos.precio_descuento` o una tabla
`descuentos`.

Requisito del mantenedor que fija el alcance:

- La oferta se define desde Admin y Vendedor (mismo perfil de permisos
  que la gestión de productos, superficie `/api/admin`).
- Es a nivel **producto** (no por línea ni por pedido).
- Es efectiva mientras el pedido está `pendiente` (antes de la OC);
  tras `aceptado` los precios quedan congelados por el snapshot de
  RN-26.

## Decisión

Patrón de negocio **precio de oferta / markdown con vigencia** (el
clásico "was–now" del retail): columnas en `productos`.

| Columna | Tipo | Restricción |
| ------- | ---- | ----------- |
| `precio_descuento` | `NUMERIC(10,2) NULL` | `CHECK (precio_descuento IS NULL OR precio_descuento < precio)` |
| `descuento_desde` | `TIMESTAMPTZ NULL` | Límite abierto si NULL |
| `descuento_hasta` | `TIMESTAMPTZ NULL` | Límite abierto si NULL |

- Una sola oferta activa por producto (una fila de producto = su oferta
  vigente).
- El precio efectivo se resuelve **SIEMPRE server-side** por servicio:
  `precio_efectivo(p, now) = precio_descuento` si
  `now ∈ [descuento_desde, descuento_hasta]` (con NULL = intervalo
  abierto); `precio` en caso contrario.

Aplicación en el flujo:

- El catálogo expone `precio_efectivo`, `en_descuento` y
  `descuento_porcentaje` calculados.
- Sort `con_descuento` (RN-07): productos con oferta vigente, mayor
  porcentaje primero; empate resuelto por `precio_efectivo` ascendente.
- Carrito y snapshot de pedido: `pedido_items.precio_unitario` = precio
  efectivo al agregar/crear/editar (solo `pendiente`); nueva columna de
  snapshot `pedido_items.precio_lista` = precio de lista del momento
  (para mostrar el ahorro).
- `pedidos.total` sigue siendo la suma de subtotales (la reserva de
  "total ≠ subtotal" era para descuento por pedido, rechazado abajo).
- Editar líneas de un pedido `pendiente` re-snapshotea al precio
  efectivo vigente en ese momento. No hay re-pricing tras `aceptado`.

## Alternativas

| Alternativa | Por qué se descarta |
| ----------- | ------------------- |
| Descuento porcentual dinámico sin precio final | Ambigüedad de redondeo en `NUMERIC(10,2)`: el precio final nunca es exacto ni auditable. |
| Descuento por línea/pedido negociado por staff | El requisito es "sobre productos"; añade auditoría y UI de negociación fuera del MVP (futuro B2B). |
| Cupones / reglas de carrito | Módulo de marketing completo, fuera de alcance del MVP. |
| Tabla `descuentos` con historial de campañas | Sobre-ingeniería para una sola oferta activa por producto; el historial de cambios lo cubre la auditoría de staff (ver `02-security.md`). |

## Consecuencias

- Positivas: sort y badge simples (índice parcial opcional); el
  snapshot inmutable garantiza que los pedidos previos no cambian al
  modificar una oferta.
- Negativas: mostrar el "ahorro" exige el snapshot `precio_lista` en
  `pedido_items`; cambiar una oferta NO recalcula los pedidos
  `pendiente` existentes hasta que estos se editen (los precios de
  líneas ya creadas permanecen hasta el re-snapshot explícito).
