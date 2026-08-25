# Casos de prueba

Catálogo de casos derivados de las reglas de negocio y casos de uso.
Convención: `TC-<fuente>-<n>` donde `<fuente>` es el ID de la regla o caso
de uso. La columna endpoint se completa al diseñar la API
(`architecture/01-api-design.md`).

> Estado: **semilla previa al diseño de API**. Los escenarios quedan fijos
> por regla; su binding a endpoints se cierra con cada change.

## Autenticación y cuenta

| ID | Escenario | Esperado | Endpoint |
| -- | --------- | -------- | -------- |
| TC-RN15-01 | Contraseña sin mayúscula / número / especial / <8 chars | Rechazo detallando política | TBD |
| TC-AUTH05-01 | Login válido → happy path, registra `last_login_at` | 200 + cookies | TBD |
| TC-AUTH05-02 | Login con contraseña incorrecta | Error específico sin revelar existencia del email | TBD |
| TC-AUTH05-03 | Login sobre cuenta `is_active=false` | Ofrece reactivación (UC-C10) | TBD |
| TC-C05-01 | Cambio de contraseña con actual correcta invalida refresh tokens activos | Sesiones previas mueren | TBD |
| TC-BOOT-01 | Primer arranque con `ADMIN_INITIAL_*` crea admin | Creado con `must_change_password` | TBD |
| TC-BOOT-02 | Segundo arranque (ya existe admin) | No-op idempotente | TBD |
| TC-RN34-01 | Carrito sobrevive logout y login en otro dispositivo | Líneas intactas | TBD |

## Catálogo

| ID | Escenario | Esperado | Endpoint |
| -- | --------- | -------- | -------- |
| TC-RN01-01 | Producto sin categoría | Rechazo (mínimo una) | TBD |
| TC-RN20-01 | Slug duplicado en producto/categoría/tag | Rechazo por unicidad | TBD |
| TC-RN23-01 | Línea con unidad no registrada para el producto | Rechazo | TBD |
| TC-RN31-01 | Producto oculto no aparece en catálogo/búsqueda pública | Invisible públicamente, visible al staff | TBD |
| TC-RN32-01 | Producto eliminado lógicamente mantiene referencias históricas resueltas | Pedidos/OC/calificaciones íntegros | TBD |
| TC-RN24-01 | Vendedor da de alta producto/tags; Comprador intenta lo mismo | Staff OK; comprador 403 | TBD |

## Búsqueda y orden

| ID | Escenario | Esperado | Endpoint |
| -- | --------- | -------- | -------- |
| TC-RN04-01 | Texto + categoría + tags combinados en una consulta | Intersección correcta | TBD |
| TC-RN07-01 | Cada uno de los 7 ordenamientos devuelve el orden esperado | Orden verificado | TBD |
| TC-RN30-01 | Apertura de detalle desde búsqueda suma punto; visita directa no | Solo origen=búsqueda puntúa | TBD |
| TC-RN08-01 | F5 dentro de ventana no incrementa visitas | Contador estable | TBD |
| TC-RN08-02 | Visita fuera de ventana (config `VISIT_DEDUP_WINDOW_HOURS`) sí incrementa | Contador +1 | TBD |
| TC-RN21-01 | Promedio 4.15 renderiza 4 estrellas + fracción de la quinta | Valor fraccional exacto | TBD |

## Favoritos

| ID | Escenario | Esperado | Endpoint |
| -- | --------- | -------- | -------- |
| TC-RN09-01 | Guardar/quitar favorito actualiza contador (+1/−1) | Piso cero respetado | TBD |

## Pedidos

| ID | Escenario | Esperado | Endpoint |
| -- | --------- | -------- | -------- |
| TC-RN28-01 | Editar/eliminar pedido solo en `pendiente`; aceptado/rechazado → rechazo | 409/422 según corresponda | TBD |
| TC-RN28-02 | Duplicar pedido rechazado genera nuevo pendiente editable con motivo visible | Nuevo pedido creado | TBD |
| TC-RN18-01 | Comprador intenta autogenerar orden de compra | Prohibido (solo Admin/Vendedor) | TBD |
| TC-RN29-01 | Consolidar pedidos de compradores distintos | Rechazo (mismo comprador only) | TBD |
| TC-RN29-02 | Consolidar N pendientes del mismo comprador → 1 OC | Totales sumados, todos `aceptado` | TBD |
| TC-RN27-01 | Reasignación de pedido pendiente entre vendedores deja auditoría | Registro quién/cuándo/desde-quién | TBD |
| TC-RN26-01 | Pedido persiste subtotal, total, fecha y creador | Campos completos | TBD |

## Calificaciones

| ID | Escenario | Esperado | Endpoint |
| -- | --------- | -------- | -------- |
| TC-RN33-01 | Calificar sin pedido aceptado del producto | Rechazo | TBD |
| TC-RN33-02 | Calificar con pedido aceptado que incluye el producto | Aceptado; promedio recalculado | TBD |

## Panel admin

| ID | Escenario | Esperado | Endpoint |
| -- | --------- | -------- | -------- |
| TC-AUTH10-01 | Token de tienda contra endpoint admin (y viceversa) | 401/403 por audiencia | TBD |
| TC-AUTH12-01 | Desactivar/reactivar usuario desde admin togglea `is_active` conservando datos | Historial íntegro | TBD |
