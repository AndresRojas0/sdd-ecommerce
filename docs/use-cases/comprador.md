# Casos de uso — Comprador (usuario autenticado)

Actor: usuario autenticado con rol Comprador. Incluye todo lo del
[visitante anónimo](visitante-anonimo.md) y los casos comunes de
[cuenta](cuenta.md).

## Favoritos

| ID | Caso de uso | Notas |
| -- | ----------- | ----- |
| UC-B01 | Agregar producto a favoritos | Incrementa contador de guardados (RN-09). |
| UC-B02 | Quitar producto de favoritos | Decrementa contador, piso cero (RN-09). |
| UC-B03 | Consultar sus favoritos | Solo los propios. |

## Pedidos

| ID | Caso de uso | Notas |
| -- | ----------- | ----- |
| UC-B04 | Armar carrito | Selecciona productos con cantidades en la unidad de venta (RN-23); previsualiza subtotal/total (RN-12). |
| UC-B05 | Crear pedido a partir del carrito | Genera pedido en estado inicial; registra fecha y creador (RN-26). |
| UC-B06 | Editar pedido | Solo mientras NO fue confirmado como orden de compra (RN-18): cambia cantidades o productos. |
| UC-B07 | Eliminar pedido | Solo pre-confirmación; si opta por darse de baja puede eliminarlos también (RN-19). |
| UC-B08 | Consultar sus pedidos y su estado | Ve el ciclo Carrito → Pedido → Orden de compra (RN-18) con fecha de cada paso. |

## Calificaciones

| ID | Caso de uso | Notas |
| -- | ----------- | ----- |
| UC-B09 | Calificar producto | 1..5 estrellas; alimenta el promedio fraccional (RN-21). |
| UC-B10 | Editar su calificación | Reemplaza su valoración previa; recalcula promedio. |

> Regla abierta a definir: ¿se puede calificar cualquier producto o solo
> productos comprados (pedido confirmado)? Queda como decisión de negocio
> pendiente.

## Perfil

Consulta y edición de perfil/avatar según [cuenta](cuenta.md)
(UC-C05..UC-C08), más darse de baja con destino de pedidos (UC-C09).
