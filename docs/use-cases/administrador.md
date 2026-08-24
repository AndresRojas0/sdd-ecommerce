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
| UC-AD06 | Listar / buscar / filtrar productos | Por categoría, tag, texto, etc. |
| UC-AD07 | Ver producto | Detalle completo. |
| UC-AD08 | Editar producto | CRUD completo (RN-24). |
| UC-AD09 | Eliminar producto | **Borrado lógico** con historial preservado (RN-32): sale de catálogo y altas nuevas; sus referencias históricas se resuelven intactas. |
| UC-AD10 | Ocultar / despublicar producto | **Incorporado** (RN-31): reversible; oculto = fuera de catálogo y búsqueda pública, permanece en DB y visible al staff. |
| UC-AD11 | Ver estadísticas básicas | Contadores del producto: visitas con origen (RN-08), búsquedas/relevancia (RN-30), guardados (RN-09), promedio/cantidad de calificaciones (RN-21). |

## Pedidos de producto (ABM completo)

Estados del pedido: `pendiente de validación`, `aceptado`, `rechazado`
(ver ciclo de vida en `domain/domain-model.md`).

| ID | Caso de uso | Notas |
| -- | ----------- | ----- |
| UC-AD12 | Mostrar pedidos validados | Ya aceptados, con su orden de compra vinculada. |
| UC-AD13 | Listar pendientes de validación | Cola operativa de trabajo. |
| UC-AD14 | Ver rechazados | Historial de rechazos. |
| UC-AD15 | Aceptar pedido → generar orden de compra | RN-18; deja el pedido inmutable para el comprador. |
| UC-AD16 | Rechazar pedido | Con motivo registrado; visible para el comprador en sus pedidos (UC-B08). |
| UC-AD17 | Corregir nombre | Corrige el nombre del producto en la línea antes de validar. |
| UC-AD18 | Normalizar unidad/nombre | Ajusta unidad de venta o denominación a los valores del registro (RN-23). |
| UC-AD19 | Consolidar pedidos en una sola orden de compra | Vincula uno o más pedidos `pendientes` entre sí para validarlos juntos como **una única** orden de compra (RN-29). Restricción: solo pedidos del mismo comprador creador. |

## Vendedores

| ID | Caso de uso | Notas |
| -- | ----------- | ----- |
| UC-AD20 | Listar vendedores | Con estado de cuenta. |
| UC-AD21 | Buscar vendedores | Por email o display-name. |
| UC-AD22 | Ver perfil de vendedor | Fecha de creación, último login. |
| UC-AD23 | Activar / desactivar vendedor | Toggle `is_active`; al desactivarse aplican las reglas de ADR-007/RN-27. |
| UC-AD24 | Ver métricas del vendedor | Cantidad de pedidos gestionados y órdenes de compra emitidas. |

## Gestión derivada

- Reasignar pedido pendiente entre vendedores activos (RN-27, ADR-007).
- Reactivar cuentas dadas de baja (equivale manual de UC-C10).
