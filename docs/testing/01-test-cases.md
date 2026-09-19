# Casos de prueba

Catálogo de casos derivados de las reglas de negocio y casos de uso.
Convención: `TC-<fuente>-<n>` donde `<fuente>` es el ID de la regla o caso
de uso. La columna endpoint se completa al diseñar la API
(`architecture/01-api-design.md`).

> Estado: **binding cerrado** contra `architecture/01-api-design.md`
> (esquema `S-*` tienda / `A-*` admin). Los escenarios quedan fijos
> por regla; los endpoints de features nuevas se agregan con cada change.

## Autenticación y cuenta

| ID | Escenario | Esperado | Endpoint |
| -- | --------- | -------- | -------- |
| TC-RN15-01 | Contraseña sin mayúscula / número / especial / <8 chars | Rechazo detallando política | S-AUTH-01 |
| TC-AUTH05-01 | Login válido → happy path, registra `last_login_at` | 200 + cookies | S-AUTH-02 |
| TC-AUTH05-02 | Login con contraseña incorrecta | Error específico sin revelar existencia del email | S-AUTH-02 |
| TC-AUTH05-03 | Login sobre cuenta `is_active=false` | Ofrece reactivación (UC-C10) | S-AUTH-02 |
| TC-C05-01 | Cambio de contraseña con actual correcta invalida refresh tokens activos | Sesiones previas mueren | S-CUENTA-02 |
| TC-BOOT-01 | Primer arranque con `ADMIN_INITIAL_*` crea admin | Creado con `must_change_password` | N/A — bootstrap por ENV (sin endpoint HTTP) |
| TC-BOOT-02 | Segundo arranque (ya existe admin) | No-op idempotente | N/A — bootstrap por ENV (sin endpoint HTTP) |
| TC-RN34-01 | Carrito sobrevive logout y login en otro dispositivo | Líneas intactas | S-CART-01 |

## Catálogo

| ID | Escenario | Esperado | Endpoint |
| -- | --------- | -------- | -------- |
| TC-RN01-01 | Producto sin categoría | Rechazo (mínimo una) | A-PROD-03 |
| TC-RN20-01 | Slug duplicado en producto/categoría/tag | Rechazo por unicidad | A-PROD-03 / A-CAT-02 / A-ETIQ-02 |
| TC-RN23-01 | Línea con unidad no registrada para el producto | Rechazo | A-PROD-03 |
| TC-RN31-01 | Producto oculto no aparece en catálogo/búsqueda pública | Invisible públicamente, visible al staff | S-CAT-01 / S-CAT-02 (vs A-PROD-01) |
| TC-RN32-01 | Producto eliminado lógicamente mantiene referencias históricas resueltas | Pedidos/OC/calificaciones íntegros | S-CAT-02 (vs A-PROD-05) |
| TC-RN24-01 | Vendedor da de alta producto/tags; Comprador intenta lo mismo | Staff OK; comprador 403 | A-PROD-03 / A-ETIQ-02 |

## Búsqueda y orden

| ID | Escenario | Esperado | Endpoint |
| -- | --------- | -------- | -------- |
| TC-RN04-01 | Texto + categoría + tags combinados en una consulta | Intersección correcta | S-CAT-01 |
| TC-RN07-01 | Cada uno de los 7 ordenamientos devuelve el orden esperado | Orden verificado | S-CAT-01 |
| TC-RN30-01 | Apertura de detalle desde búsqueda suma punto; visita directa no | Solo origen=búsqueda puntúa | S-CAT-03 |
| TC-RN08-01 | F5 dentro de ventana no incrementa visitas | Contador estable | S-CAT-03 |
| TC-RN08-02 | Visita fuera de ventana (config `VISIT_DEDUP_WINDOW_HOURS`) sí incrementa | Contador +1 | S-CAT-03 |
| TC-RN21-01 | Promedio 4.15 renderiza 4 estrellas + fracción de la quinta | Valor fraccional exacto | S-CAT-02 |

## Favoritos

| ID | Escenario | Esperado | Endpoint |
| -- | --------- | -------- | -------- |
| TC-RN09-01 | Guardar/quitar favorito actualiza contador (+1/−1) | Piso cero respetado | S-FAV-01 / S-FAV-02 |

## Pedidos

| ID | Escenario | Esperado | Endpoint |
| -- | --------- | -------- | -------- |
| TC-RN28-01 | Editar/eliminar pedido solo en `pendiente`; aceptado/rechazado → rechazo | 409/422 según corresponda | S-PED-04 / S-PED-05 |
| TC-RN28-02 | Duplicar pedido rechazado genera nuevo pendiente editable con motivo visible | Nuevo pedido creado | S-PED-06 |
| TC-RN18-01 | Comprador intenta autogenerar orden de compra | Prohibido (solo Admin/Vendedor) | S-PED-01 (401/403 en A-OC-01) |
| TC-RN29-01 | Consolidar pedidos de compradores distintos | Rechazo (mismo comprador only) | A-OC-01 |
| TC-RN29-02 | Consolidar N pendientes del mismo comprador → 1 OC | Totales sumados, todos `aceptado` | A-OC-01 |
| TC-RN27-01 | Reasignación de pedido pendiente entre vendedores deja auditoría | Registro quién/cuándo/desde-quién | A-PED-07 |
| TC-RN27-02 | Auditoría de reasignación con antes/después | `staff_audits` guarda `vendedor_id` previo y nuevo (consulta vía GET /admin/audit) | A-PED-07 + A-AUD-01 |
| TC-RN26-01 | Pedido persiste subtotal, total, fecha y creador | Campos completos | S-PED-03 |

## Calificaciones

| ID | Escenario | Esperado | Endpoint |
| -- | --------- | -------- | -------- |
| TC-RN33-01 | Calificar sin pedido aceptado del producto | Rechazo | S-CAL-01 |
| TC-RN33-02 | Calificar con pedido aceptado que incluye el producto | Aceptado; promedio recalculado | S-CAL-01 / S-CAL-02 |

## Panel admin

| ID | Escenario | Esperado | Endpoint |
| -- | --------- | -------- | -------- |
| TC-AUTH10-01 | Token de tienda contra endpoint admin (y viceversa) | 401/403 por audiencia | A-AUTH-01 / A-AUTH-04 (aislamiento de audiencia) |
| TC-AUTH12-01 | Desactivar/reactivar usuario desde admin togglea `is_active` conservando datos | Historial íntegro | A-USR-04 |
| TC-AUTH10-02 | Operaciones admin por grupo de router rechazan token de tienda (comprador) y aceptan token admin | 401/403 vs operativos | A-PROD-03, A-CAT-02, A-ETIQ-02, A-UNID-02, A-COL-02, A-PED-03, A-STK-04, A-DASH-01 |

## Descuentos (ADR-008)

| ID | Escenario | Esperado | Endpoint |
| -- | --------- | -------- | -------- |
| TC-ADR008-01 | Oferta con vigencia: efectivo en catálogo, snapshots en pedido (unit+lista), re-snapshot al editar pendiente | Precios exactos | PUT /products/{id}/discount (A-PROD-08) |
| TC-ADR008-02 | Orden con_descuento: ofertas activas primero, mayor % primero | Orden verificado | S-CAT-01 |

## Auditoría y admin (M5)

| ID | Escenario | Esperado | Endpoint |
| -- | --------- | -------- | -------- |
| TC-AUD-01 | Transición de pedido auditada (aceptar/rechazar/facturar/en-logistica/entregar) | Fila en `staff_audits` con actor, acción y estados antes/después | A-PED-04..09 + A-AUD-01 |
| TC-M5-01 | Edición de líneas de pedido solo en `pendiente` | 409 en `aceptado`; re-snapshot de precios (ADR-008) y recálculo de total; auditoría con líneas antes/después | A-PED-06 |
| TC-M5-02 | Consulta de auditoría restringida a `administrador` | Vendedor (aud admin) → 403; comprador (aud tienda) → 401/403 | A-AUD-01 |
