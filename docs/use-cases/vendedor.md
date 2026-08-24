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

| ID | Caso de uso | Notas |
| -- | ----------- | ----- |
| UC-V06 | Listar pedidos | Vista operativa de todos los pedidos generados. |
| UC-V07 | Filtrar pedidos por usuario | Por comprador creador del pedido. |
| UC-V08 | Cargar pedido en nombre de un cliente | Alta de pedido con el vendedor como operador y el cliente como creador lógico. |
| UC-V09 | Confirmar pedido y generar orden de compra | Acción exclusiva de staff (RN-18). El pedido deja de ser editable/eliminable por el comprador. |

## Darse de baja

El Vendedor puede darse de baja (UC-C09). El destino de sus órdenes de
compra está en decisión (opciones evaluadas con el negocio): se tiende a
que permanezcan asociadas a sus datos históricos y que solo la gestión
pendiente sea transferible por un Administrador. Pendiente de ADR.

## Omisión corregida respecto de la lista original

La lista original de este actor omitía el alta de productos y etiquetas,
que sí estaba confirmada como capacidad (AUTH/RN-24). Se reincorporó como
UC-V01/UC-V02.
