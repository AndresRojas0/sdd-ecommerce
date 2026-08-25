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
| UC-B04 | Armar carrito | Agregar productos con cantidad en su unidad de venta (RN-23), cambiar cantidades, quitar líneas. Carrito server-side persistente (RN-34). |
| UC-B04a | Previsualizar el pedido en el carrito | Ve subtotal por línea y total antes de confirmar (RN-12). |
| UC-B05 | Crear pedido a partir del carrito | Genera pedido en estado `pendiente de validación`; registra fecha y creador (RN-26). |
| UC-B06 | Editar pedido | Solo en estado `pendiente`: cambia cantidades o productos. |
| UC-B06a | Duplicar pedido rechazado | Crea un nuevo pedido `pendiente` copiando las líneas del rechazado para editarlas; el motivo del rechazo queda visible (RN-28). |
| UC-B07 | Eliminar pedido | Solo en estado `pendiente`; si opta por darse de baja puede eliminarlos también (RN-19). |
| UC-B08 | Consultar sus pedidos y su estado | Ve el ciclo completo con estados `pendiente` / `aceptado` (+ orden de compra) / `rechazado` (con motivo), y fecha de cada paso (RN-18, RN-28). |

## Calificaciones

| ID | Caso de uso | Notas |
| -- | ----------- | ----- |
| UC-B09 | Calificar producto | 1..5 estrellas; requiere pedido aceptado que incluya el producto (RN-33); alimenta el promedio fraccional (RN-21). |
| UC-B10 | Editar su calificación | Reemplaza su valoración previa; recalcula promedio. Misma elegibilidad RN-33. |

## Perfil

Consulta y edición de perfil/avatar según [cuenta](cuenta.md)
(UC-C05..UC-C08), más darse de baja con destino de pedidos (UC-C09).
