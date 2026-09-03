# Casos de uso — Vendedor

Actor staff con rol Vendedor (alias: atención al público / ventas).
Incluye los casos comunes de [cuenta](cuenta.md) (UC-C01..UC-C10).

> **Superficie a confirmar**: se asume que el Vendedor opera dentro del
> panel de administración (aplicación Svelte independiente, ADR-005), no en
> la tienda pública. Sus funciones son operativas, no de consumo.

## Catálogo

| ID | Caso de uso | Notas |
| -- | ----------- | ----- |
| UC-V01 | Dar de alta productos | Con título, slug, categorías, tags, descripción, componentes incluidos, datos técnicos, precio y unidad de venta (RN-24). |
| UC-V02 | Dar de alta etiquetas | Crea términos nuevos del vocabulario abierto con slug. |

## Usuarios

| ID | Caso de uso | Notas |
| -- | ----------- | ----- |
| UC-V03 | Buscar perfiles de usuarios | Búsqueda por email/display-name (RN-22). |
| UC-V04 | Consultar perfil de un usuario con todos sus pedidos | Evolución: antes era solo consulta; ahora incluye edición (UC-V05). |
| UC-V05 | Editar perfiles de usuarios | Alcance a acotar: datos de perfil; NO rol, NO contraseña. |

## Pedidos

Estados: `pendiente → aceptado (En preparación) → facturado → en_logistica → entregado` + `rechazado` terminal (RN-28). El Vendedor solo transiciona `pendiente → aceptado` y `* → rechazado`; `facturado` y posteriores son de Administrador/Logística.

| ID | Caso de uso | Notas |
| -- | ----------- | ----- |
| UC-V06 | Listar pedidos | Vista operativa de todos los pedidos generados, con columna de estado extendido y kanban (Recibido / En preparación / Facturación / Logística / Entregado). |
| UC-V07 | Filtrar pedidos por usuario | Por comprador creador del pedido. |
| UC-V08 | Cargar pedido en nombre de un cliente | Alta de pedido con el vendedor como operador y el cliente como creador lógico. |
| UC-V09 | Confirmar pedido y generar orden de compra (aceptar) | RN-18, RN-28 (`pendiente → aceptado`, Vendedor/Admin). Reserva stock (RN-35). El pedido deja de ser editable/eliminable por el comprador. |
| UC-V10 | Rechazar pedido | RN-28 (`pendiente → rechazado` o `aceptado → rechazado` con devolución de stock RN-35 `devolucion`). Con motivo visible para el comprador. |
| UC-V11 | Ver pedido facturado / en logística / entregado | Solo lectura; `facturado → en_logistica → entregado` lo operan Admin/Logística (UC-AD26/AD27, RN-28). |

## Darse de baja

El Vendedor puede darse de baja (UC-C09). Sus órdenes de compra confirmadas
quedan congeladas con su atribución original; los pedidos sin confirmar son
reasignables por un Administrador a otro vendedor activo con auditoría
(RN-27, ADR-007).

## Omisión corregida respecto de la lista original

La lista original de este actor omitía el alta de productos y etiquetas,
que sí estaba confirmada como capacidad (AUTH/RN-24). Se reincorporó como
UC-V01/UC-V02.
