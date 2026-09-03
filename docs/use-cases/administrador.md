# Casos de uso — Administrador

Actor con rol Administrador sobre el panel de administración (aplicación
Svelte independiente que consume la API, ADR-005). Su sistema de
autenticación es propio e independiente del usuario común (AUTH-10).

El primer administrador surge del bootstrap por variables de entorno
(ADR-006), no de un caso de uso de registro.

## Usuarios

| ID | Caso de uso | Notas |
| -- | ----------- | ----- |
| UC-AD01 | Listar usuarios | Paginado; incluye estado de cuenta. |
| UC-AD02 | Buscar usuarios | Por email o display-name. |
| UC-AD03 | Ver perfil de usuario | Incluye fecha de creación y último login (RN-14). |
| UC-AD04 | Activar / desactivar usuario | Toggle `is_active`. Desactivar es baja lógica impuesta (RN-17); reactivar equivale a UC-C10 manual. |
| UC-AD05 | Ver métricas del usuario | Cantidad de pedidos y de órdenes de compra generadas. |

## Productos

| ID | Caso de uso | Notas |
| -- | ----------- | ----- |
| UC-AD06 | Listar / buscar / filtrar productos | Por categoría (árbol 2N, `RN-01`/`RN-38`), subcategoría, tag, texto, colección, etc. Filtro por categoría raíz incluye sus subcategorías hijas; filtro por hoja es exacto. |
| UC-AD07 | Ver producto | Detalle completo (incluye categorías hoja asignadas y colecciones). |
| UC-AD08 | Crear / editar producto | CRUD completo (RN-24). **Debe asignar al menos una subcategoría hoja (nivel 2)**; no es válido solo el padre (`RN-38` — validación `422`). Soporta selección jerárquica padre→hijas en el form. |
| UC-AD09 | Eliminar producto | **Borrado lógico** con historial preservado (RN-32): sale de catálogo y altas nuevas; sus referencias históricas se resuelven intactas. Limpia vínculos en `coleccion_productos` por `CASCADE`. |
| UC-AD10 | Ocultar / despublicar producto | **Incorporado** (RN-31): reversible; oculto = fuera de catálogo y búsqueda pública, permanece en DB y visible al staff. |
| UC-AD11 | Ver estadísticas básicas | Contadores del producto: visitas con origen (RN-08), búsquedas/relevancia (RN-30), guardados (RN-09), promedio/cantidad de calificaciones (RN-21). |

## Categorías — árbol 2 niveles (RN-01, RN-38)

Taxonomía cerrada jerárquica de máx. 2 niveles (`categorias.parent_id`, `nivel`). Solo Admin gestiona el árbol.

| ID | Caso de uso | Notas |
| -- | ----------- | ----- |
| UC-AD06 | Gestionar categorías (árbol) | **Extendido para árbol 2N**: listar árbol (raíz + hijas), buscar por nombre/slug, ver detalle con hijas y productos asociados. **Crear categoría nivel 1** (`parent_id=NULL`, `nivel=1`) y **crear subcategoría** (`parent_id` obligatorio apuntando a nivel 1, `nivel=2`). Editar nombre/slug/color y **mover** subcategoría entre padres (solo si destino es nivel 1). Eliminar con `ON DELETE RESTRICT`: falla si tiene hijas o productos vinculados sin reasignación. Validaciones: `CHECK nivel IN (1,2)`, `CHECK parent_id IS NULL ↔ nivel=1`, trigger impide `parent_id → nivel 2` y ciclos. |

> UC-AD06 concentra la gestión del árbol; el listado de productos (UC-AD06) y el ABM de categorías comparten el mismo entry-point en el panel, con pestaña Árbol.

## Colecciones — grupos curados (RN-39)

Grupos transversales a categorías para descubrimiento/marketing. No son taxonomía ni filtro; navegación directa `/colecciones/{slug}` y bloque `destacada` en home.

| ID | Caso de uso | Notas |
| -- | ----------- | ----- |
| UC-AD29 | Listar colecciones | Paginado; incluye `destacada`, cantidad de productos y `updated_at`. Filtro por `destacada`. |
| UC-AD30 | Crear colección | `nombre UNIQUE`, `slug UNIQUE` (`RN-20`), `descripcion` (nullable), `imagen` (nullable), `destacada=false` por defecto. Slug auto-generado y validado único. |
| UC-AD31 | Editar colección | Edita nombre/slug/descripcion/imagen. Cambio de slug mantiene unicidad; si colección tiene productos, no afecta vínculos. |
| UC-AD32 | Eliminar colección | `DELETE` físico; `ON DELETE CASCADE` limpia `coleccion_productos` sin afectar productos. Confirmación requerida. |
| UC-AD33 | Asignar / desasignar productos a colección | N:M `coleccion_productos (coleccion_id, product_id, added_at, orden)`. Agregar quita duplicados (`PK` compuesta). Reordenar vía `orden` (drag & drop). Validación: producto debe existir y estar no eliminado (`deleted_at IS NULL`). |
| UC-AD34 | Toggle destacada | `PATCH destacada` para home. Listado de destacadas usa índice parcial `WHERE destacada=true`. Sin límite en MVP; sugerido máx. 6 para UI. |

## Pedidos de producto (ABM completo)

Estados del pedido: `pendiente → aceptado (En preparación) → facturado → en_logistica → entregado`, más `rechazado` terminal (RN-28, ver ciclo de vida en `domain/domain-model.md`). Cada transición de stock genera `movimientos_stock` (RN-35).

| ID | Caso de uso | Notas |
| -- | ----------- | ----- |
| UC-AD12 | Mostrar pedidos validados | Ya aceptados (y posteriores), con su orden de compra vinculada. Incluye facturados, en logística y entregados. |
| UC-AD13 | Listar pendientes de validación | Cola operativa de trabajo (`pendiente`). |
| UC-AD14 | Ver rechazados | Historial de rechazos (`rechazado` terminal). |
| UC-AD15 | Aceptar pedido → generar orden de compra | RN-18, RN-28 (`pendiente → aceptado`, Vendedor/Admin). Reserva stock (RN-35): `disponible −= cantidad`, `reservada += cantidad`. Deja el pedido inmutable para el comprador. |
| UC-AD16 | Rechazar pedido | Con motivo registrado; visible para el comprador en sus pedidos (UC-B08). `pendiente → rechazado` sin efecto stock; `aceptado → rechazado` libera reserva (RN-35 `devolucion`). |
| UC-AD17 | Corregir nombre | Corrige el nombre del producto en la línea antes de validar. |
| UC-AD18 | Normalizar unidad/nombre | Ajusta unidad de venta o denominación a los valores del registro (RN-23). |
| UC-AD19 | Consolidar pedidos en una sola orden de compra | Vincula uno o más pedidos `pendientes` entre sí para validarlos juntos como **una única** orden de compra (RN-29). Restricción: solo pedidos del mismo comprador creador. Al facturar la OC, todos avanzan juntos a `facturado` (RN-36). |
| UC-AD25 | Facturar pedido / orden de compra | RN-28 (`aceptado → facturado`, solo Administrador) y RN-36. Genera `facturas` con `numero_fiscal` único, `total` snapshot de la OC y `created_by`. Confirma deducción de stock (RN-35 `confirmacion`: `reservada −= cantidad`). Falla si la OC ya fue facturada o si no todos sus pedidos están en `aceptado`. |
| UC-AD26 | Pasar a logística | RN-28 (`facturado → en_logistica`, Administrador/Logística). Sin efecto stock. |
| UC-AD27 | Marcar entregado | RN-28 (`en_logistica → entregado`, Administrador/Logística). Estado terminal de éxito; sin efecto stock. |
| UC-AD28 | Ver totales del día | RN-37. Widget de dashboard (no columna kanban): `SUM(facturas.total)` del día corriente. Solo facturas cuentan. |

## Vendedores

| ID | Caso de uso | Notas |
| -- | ----------- | ----- |
| UC-AD20 | Listar vendedores | Con estado de cuenta. |
| UC-AD21 | Buscar vendedores | Por email o display-name. |
| UC-AD22 | Ver perfil de vendedor | Fecha de creación, último login. |
| UC-AD23 | Activar / desactivar vendedor | Toggle `is_active`; al desactivarse aplican las reglas de ADR-007/RN-27. |
| UC-AD24 | Ver métricas del vendedor | Cantidad de pedidos gestionados y órdenes de compra emitidas. |

## Kanban de pedidos y dashboard

Tablero kanban con 5 columnas de estado + widget de totales:

| Columna | Estado | Origen |
|---------|--------|--------|
| Recibido | `pendiente` | Pedidos recién confirmados por el comprador |
| En preparación | `aceptado` | Tras UC-AD15 (reserva stock RN-35) |
| Facturación | `facturado` | Tras UC-AD25 (factura RN-36, confirmación RN-35) |
| Logística | `en_logistica` | Tras UC-AD26 |
| Entregado | `entregado` | Tras UC-AD27 (terminal de éxito) |

Más historial de `rechazado` (terminal con motivo) y **widget Totales del día** (UC-AD28, RN-37) fuera del kanban: suma de `facturas.total` del día, no columna.

## Gestión derivada

- Reasignar pedido pendiente entre vendedores activos (RN-27, ADR-007).
- Reactivar cuentas dadas de baja (equivale manual de UC-C10).
- Stock y movimientos: el staff consulta `stock` por producto y el historial `movimientos_stock` (RN-35); ajustes manuales fuera de MVP.
