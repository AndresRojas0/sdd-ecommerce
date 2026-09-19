# Diseño de API (REST)

Contratos entre frontends y backend. El estilo es REST (ADR-004) con
superficies separadas por audiencia.

## Estado

Diseño de endpoints **completado** para el MVP. Cobertura: todos los UC
de los cinco actores tienen ≥1 endpoint (ver matriz §7); los ítems
diferidos o fuera de alcance están listados en §8. Los conflictos
detectados entre documentos se listan en §9 sin resolver en este doc.

## Principios ya decididos

- Un solo backend FastAPI con dos superficies de endpoints:
  - `/api/store/...` → audiencia tienda (pública + comprador autenticado).
  - `/api/admin/...` → audiencia administrador/vendedor, tokens con
    audiencia propia (ADR-005).
- Autenticación por cookies JWT; refresh token rotativo en
  `Path=/auth/refresh` (tienda) y path equivalente propio para admin.
- Errores HTTP consistentes: códigos estándar + cuerpo de error estructurado
  para mapear a los mensajes de login éxito/error (AUTH-05).

## Convenciones globales

### Autenticación (ADR-003, AUTH-09, AUTH-10)

| Aspecto | Tienda (`/api/store`) | Admin (`/api/admin`) |
| --- | --- | --- |
| Access token | JWT 15 min, `aud=store`, claims `sub`, `role`, `iat`, `exp` | JWT 15 min, `aud=admin`, mismos claims |
| Refresh token | 30 días, rotativo, hash SHA-256 en `refresh_tokens` con `family_id` | Ídem, pero `aud=admin` |
| Cookies | `HttpOnly`, `Secure`, `SameSite=Lax`; refresh con `Path=/api/store/auth/refresh` | Nombres de cookie propios; refresh con `Path=/admin/auth/refresh` |
| Roles | anónimo, `comprador` | `vendedor`, `administrador` (y `comprador` solo para ser denegado) |

Nota de implementación: las rutas del backend no llevan prefijo `/api`
(p. ej. `/admin/orders`, `/auth/login`). El mapeo completo diseño→ruta real
está en `docs/reviews/2026-09-16-verificacion-api-vs-codigo.md`.

- Un token de tienda no es válido en admin y viceversa (TC-AUTH10-01).
- Logout revoca la familia completa de refresh tokens (RN de
  `refresh_tokens.family_id`).
- Roles: columna `users.role` con valores
  `('comprador','vendedor','administrador')`; no hay tabla `roles`.
  "Logística" no existe como rol en MVP (ver §9.2).

### Errores

Cuerpo estructurado uniforme, con mensajes explícitos para mapear
AUTH-05:

```json
{ "error": { "code": "pedido_no_editable", "message": "...", "details": {} } }
```

Semántica de códigos: `401` sin sesión o token inválido; `403` sesión
válida sin permiso (rol o audiencia); `404` recurso inexistente o no
visible para el rol; `409` conflicto de estado de máquina o stock
insuficiente (RN-28/35); `422` validación de negocio fallida
(categoría hoja RN-01, slug único RN-20, unidad RN-23, elegibilidad
RN-33, consolidación RN-29).

### Paginación y filtros

- Colecciones: `?page=&per_page=` (default `per_page=20`, máx 100).
  Respuesta: `{ "items": [...], "total": n, "page": n, "per_page": n }`.
- Filtros por query string; sin `POST` de búsqueda.
- `productos` admite combinación en intersección (RN-04/05):
  `q` (nombre + datos técnicos), `categoria` (slug hoja),
  `etiquetas` (slugs, coma), `orden` (RN-07):
  `relevancia | precio_asc | precio_desc | mas_vendidos | mejor_calificados | mas_nuevos | mas_guardados`.
  `orden=con_descuento` activo (ADR-008): mayor % primero, empate por
  precio efectivo ascendente (§8.1).

### Idempotencia y estado

- Carrito: una línea por producto (`UNIQUE (carrito_id, product_id)`);
  agregar un producto existente suma cantidad (merge).
- Visitas: dedup server-side en ventana `VISIT_DEDUP_WINDOW_HOURS`
  (default 24 h) por `user_id` o `visitor_cookie` (ADR-001, RN-08/30).
- Estados de pedido: solo transiciones de RN-28 (§6.3); OC sin columna de
  estado — estado derivado (RN-36, §9.7).

---

## 1. Superficie tienda — auth y cuenta (`/api/store`)

| ID | Endpoint | Auth | Descripción | Errores | Refs |
| --- | --- | --- | --- | --- | --- |
| S-AUTH-01 | `POST /api/store/auth/register` | anónimo | Crea `users` rol `comprador`; valida política AUTH-04 | 422 política/slug email duplicado | UC-C01, RF-01/16, AUTH-04 |
| S-AUTH-02 | `POST /api/store/auth/login` | anónimo | Login por email único (RN-14); setea cookies; registra `last_login_at`; si `is_active=false` responde ofreciendo reactivación (UC-C10) sin revelar existencia de email | 401 credenciales; 423 cuenta inactiva | UC-C02, AUTH-03/05, TC-AUTH05-01..03 |
| S-AUTH-03 | `POST /api/store/auth/refresh` | cookie refresh | Rotación: emite nuevo par, revoca el anterior; reuso revoca familia completa | 401 token reusado/expirado | ADR-003, AUTH-09 |
| S-AUTH-04 | `POST /api/store/auth/logout` | sesión | Revoca familia de refresh; limpia cookies | — | UC-C03 |
| S-AUTH-05 | `GET /api/store/auth/me` | sesión | Perfil propio (`users` sin `password_hash`) | 401 | UC-C08 |
| S-CUENTA-01 | `PATCH /api/store/cuenta/perfil` | sesión | Edita `display_name` (avatar: §8.4) | 422 | UC-C06, RF-28 |
| S-CUENTA-02 | `POST /api/store/cuenta/password` | sesión | Cambio de contraseña con actual correcta; invalida todos los refresh activos | 422 política; 401 actual incorrecta | UC-C05, RF-29, TC-C05-01 |
| S-CUENTA-03 | `POST /api/store/cuenta/desactivar` | sesión | Baja lógica `is_active=false`, conserva datos (RN-17/19) | — | UC-C09, RF-18, AUTH-07 |
| S-CUENTA-04 | `POST /api/store/cuenta/reactivar` | anónimo | Reactivación nativa con credenciales válidas (ADR-002) | 401/422 | UC-C10, RF-31, TC-AUTH05-03 |

Recuperación de contraseña: diferida (RF-17/AUTH-06/UC-C04). El shape del
endpoint se definirá al implementarla; no hay contrato en MVP.

## 2. Superficie tienda — catálogo público

| ID | Endpoint | Auth | Descripción | Errores | Refs |
| --- | --- | --- | --- | --- | --- |
| S-CAT-01 | `GET /api/store/productos` | anónimo | Búsqueda/filtros/orden/paginación (§Convenciones); solo `estado_publicacion='publicado'` y `deleted_at IS NULL` (RN-31/32); incluye contadores cacheados y `calificacion_promedio` fraccional | 422 filtros inválidos | UC-A01..A07, RF-02..05/09, RN-04/05/07, TC-RN04-01/07-01 |
| S-CAT-02 | `GET /api/store/productos/{slug}` | anónimo | Detalle por slug SEO (RF-20); registra visita (S-CAT-03) salvo dedup activo; 404 si oculto/eliminado para público | 404 | UC-A08, RF-20, RN-31/32, TC-RN32-01, TC-RN21-01 |
| S-CAT-03 | `POST /api/store/productos/{id}/visitas` | anónimo/sesión | Registra `visitas` con `origen` (`directa`|`busqueda`); emite/usa cookie first-party UUID del visitante (ADR-001); dedup en ventana; solo `busqueda` puntúa para ese contador (RN-30) | 404 producto no público | UC-A08, RF-12, RN-08/30, ADR-001, TC-RN30-01/08-01/08-02 |
| S-CAT-04 | `GET /api/store/etiquetas?q=` | anónimo | Autocomplete de `etiquetas` (índice trgm, RN-03) | — | UC-A05, RF-05 |
| S-CAT-05 | `GET /api/store/categorias` | anónimo | Árbol de `categorias` (nivel 1 + hojas nivel 2, RN-01/38) | — | UC-A04 |
| S-CAT-06 | `GET /api/store/colecciones/{slug}` | anónimo | Contenido público de `colecciones` con productos ordenados por `orden` | 404 | RN-39 (superficie pública implícita en el diseño de slugs) |

## 3. Superficie tienda — favoritos, carrito, pedidos, calificaciones

| ID | Endpoint | Auth | Descripción | Errores | Refs |
| --- | --- | --- | --- | --- | --- |
| S-FAV-01 | `POST /api/store/favoritos` | comprador | Alta en `favoritos`; `guardados_count +1` | 409 duplicado | UC-B01, RF-06, RN-09, TC-RN09-01 |
| S-FAV-02 | `DELETE /api/store/favoritos/{product_id}` | comprador | Baja; `guardados_count −1` con piso 0 | 404 | UC-B02, RN-09, TC-RN09-01 |
| S-FAV-03 | `GET /api/store/favoritos` | comprador | Lista propia con datos de producto | — | UC-B03 |
| S-CART-01 | `GET /api/store/carrito` | comprador | Único carrito del usuario (RN-34) con líneas, `precio_unitario` snapshot y preview de totales (RN-12) | — | UC-B04a, RF-14, TC-RN34-01 |
| S-CART-02 | `POST /api/store/carrito/items` | comprador | Agrega línea (merge si existe, RN-23 cantidades fraccionarias > 0); snapshot de precio | 404/422 producto no público | UC-B04, AUTH-01 |
| S-CART-03 | `PATCH /api/store/carrito/items/{product_id}` | comprador | Cambia cantidad | 422 cantidad ≤ 0 | UC-B04 |
| S-CART-04 | `DELETE /api/store/carrito/items/{product_id}` | comprador | Quita línea | 404 | UC-B04 |
| S-PED-01 | `POST /api/store/pedidos` | comprador | Crea `pedidos` `pendiente` desde el carrito; snapshot de líneas en `pedido_items` (RN-26); el comprador nunca genera OC | 409 carrito vacío; stock solo se valida al aceptar | UC-B05, RF-07, RN-26/34, TC-RN18-01, TC-RN26-01 |
| S-PED-02 | `GET /api/store/pedidos` | comprador | Lista propia con ciclo de estado completo; datos de factura vía OC asociada (RN-29/36) | — | UC-B08 |
| S-PED-03 | `GET /api/store/pedidos/{id}` | comprador (dueño) | Detalle con líneas, estados y motivo de rechazo si existe | 404 ajeno | UC-B08, TC-RN26-01 |
| S-PED-04 | `PATCH /api/store/pedidos/{id}` | comprador (dueño) | Edita líneas solo en `pendiente` | 409/422 estado ≠ pendiente | UC-B06, RF-30, TC-RN28-01 |
| S-PED-05 | `DELETE /api/store/pedidos/{id}` | comprador (dueño) | Elimina solo `pendiente` | 409/422 ídem | UC-B07, RF-30, TC-RN28-01 |
| S-PED-06 | `POST /api/store/pedidos/{id}/duplicar` | comprador (dueño) | Duplica pedido `rechazado` como nuevo `pendiente` editable (líneas duplicadas permitidas, sin UNIQUE) | 409 estado no rechazado | UC-B06a, RF-30, TC-RN28-02 |
| S-CAL-01 | `POST /api/store/productos/{id}/calificaciones` | comprador | Alta de `calificaciones` 1..5; elegibilidad RN-33: EXISTS pedido `aceptado` con el producto | 422 no elegible | UC-B09, RF-08, RN-33, TC-RN33-01/02 |
| S-CAL-02 | `PATCH /api/store/productos/{id}/calificaciones` | comprador (autor) | Edita estrellas (UNIQUE user+producto); recalcula `calificacion_promedio` | 404 sin calificación | UC-B10, RN-21, TC-RN33-02 |

## 4. Superficie admin (`/api/admin`) — auth y usuarios

Login/cookies propios y aislados (AUTH-10, ADR-003/005). El bootstrap
inicial es por `ADMIN_INITIAL_*` al arranque del backend (BOOT-01/03,
ADR-006): no es un endpoint HTTP.

| ID | Endpoint | Auth | Descripción | Errores | Refs |
| --- | --- | --- | --- | --- | --- |
| A-AUTH-01 | `POST /admin/auth/login` | anónimo admin | Login con `aud=admin`, cookies propias; exige cambio si `must_change_password` | 401/423 | AUTH-10/11, TC-AUTH10-01 |
| A-AUTH-02 | `POST /admin/auth/refresh` | cookie admin | Rotación idéntica a S-AUTH-03 con `aud=admin` | 401 | ADR-003/005 |
| A-AUTH-03 | `POST /admin/auth/logout` | sesión admin | Revoca familia admin | — | UC-C03 |
| A-AUTH-04 | `GET /admin/auth/me` | sesión admin | Perfil staff | 401 | — |
| A-AUTH-05 | `POST /admin/auth/change-password-force` | cookie admin | Cambio forzado (must_change_password); revoca tokens de ambas audiencias | 401/422 | BOOT-03 |
| A-USR-01 | `GET /api/admin/usuarios` | staff | Lista/búsqueda/filtro (rol, `is_active`, q) | — | UC-AD01/02, UC-V03 |
| A-USR-02 | `GET /api/admin/usuarios/{id}` | staff | Detalle de perfil | 404 | UC-AD03, UC-V04 |
| A-USR-03 | `PATCH /api/admin/usuarios/{id}` | staff | Edición acotada de datos de perfil: NO rol, NO contraseña (alcance a confirmar en vendedor.md) | 422 | UC-AD05, UC-V05, RF-32 |
| A-USR-04 | `PATCH /api/admin/usuarios/{id}/estado` | `administrador` | Toggle `is_active` conservando datos (RN-17/19, ADR-007) | 404 | UC-AD04/23, AUTH-12, TC-AUTH12-01 |
| A-USR-05 | `GET /api/admin/usuarios/{id}/metricas` | staff | Métricas del usuario (pedidos, gastos) | 404 | UC-AD05/24 |
| A-USR-06 | `GET /api/admin/usuarios/{id}/pedidos` | staff | Todos los pedidos del usuario | — | UC-V04 |

## 5. Superficie admin — catálogo

| ID | Endpoint | Auth | Descripción | Errores | Refs |
| --- | --- | --- | --- | --- | --- |
| A-PROD-01 | `GET /api/admin/productos` | staff | Lista/búsqueda/filtros: incluye ocultos y eliminados lógicos (RN-31/32 visibles al staff) | — | UC-AD06, TC-RN31-01 |
| A-PROD-02 | `GET /api/admin/productos/{id}` | staff | Detalle completo | 404 | UC-AD07 |
| A-PROD-03 | `POST /api/admin/productos` | staff | Alta: ≥1 categoría hoja nivel 2 (422, RN-01), slug único (RN-20), unidad registrada (RN-23), `precio > 0` (RN-11); `imagen` queda NULL en MVP (RN-13) | 422 | UC-AD08/V01, TC-RN01-01/20-01/23-01/24-01 |
| A-PROD-04 | `PATCH /api/admin/productos/{id}` | staff | Edición de campos; revalida RN-01/20/23 | 422/409 | UC-AD08 |
| A-PROD-05 | `DELETE /api/admin/productos/{id}` | staff | Baja lógica (`deleted_at`); conserva historial resuelto de pedidos/OC/calificaciones (RN-32) | 404 | UC-AD09, TC-RN32-01 |
| A-PROD-06 | `PATCH /api/admin/productos/{id}/publicacion` | staff | `publicado` ⇄ `oculto` (RN-31) | 404 | UC-AD10, TC-RN31-01 |
| A-PROD-07 | `GET /api/admin/productos/{id}/estadisticas` | staff | Contadores cacheados (visitas/guardados/búsquedas/calificaciones) | 404 | UC-AD11 |
| A-PROD-08 | `PUT /api/admin/productos/{id}/descuento` | staff | Define/quita vigencia: `precio_descuento`, `descuento_desde/hasta` (ADR-008; CHECK < precio) | 422 precio ≥ lista | ADR-008, UC-AD08 |
| A-PROD-09 | `DELETE /api/admin/productos/{id}/descuento` | staff | Limpia la oferta activa | 404 sin oferta | ADR-008 |
| A-ETIQ-01 | `GET /api/admin/etiquetas` | staff | Lista completa del vocabulario abierto (RN-02) | — | UC-V02 |
| A-ETIQ-02 | `POST /api/admin/etiquetas` | staff | Alta de etiqueta; slug único | 422 | UC-V02, RN-02/20 |
| A-UNID-01 | `GET /api/admin/unidades` | staff | Registro abierto de unidades (RN-23) | — | UC-V01 |
| A-UNID-02 | `POST /api/admin/unidades` | staff | Alta de unidad | 422 | RN-23, TC-RN23-01 |
| A-CAT-01 | `GET /api/admin/categorias` | staff | Árbol completo | — | UC-AD06 (gestión de árbol) |
| A-CAT-02 | `POST /api/admin/categorias` | staff | Alta; slug único; profundidad máx 2 (RN-01/38) | 422/409 | RN-20 |
| A-CAT-03 | `PATCH /api/admin/categorias/{id}` | staff | Edición/repunto con validación de padre nivel 1 | 422/409 | UC-AD06 |
| A-CAT-04 | `DELETE /api/admin/categorias/{id}` | staff | Baja; `RESTRICT` si tiene hijos o productos | 409 | UC-AD06 |
| A-COL-01 | `GET /api/admin/colecciones` | staff | Lista (RN-39) | — | UC-AD29 |
| A-COL-02 | `POST /api/admin/colecciones` | staff | Alta; slug único | 422 | UC-AD30 |
| A-COL-03 | `PATCH /api/admin/colecciones/{id}` | staff | Edición | 404/422 | UC-AD31 |
| A-COL-04 | `DELETE /api/admin/colecciones/{id}` | staff | Baja (CASCADE de vínculos) | 404 | UC-AD32 |
| A-COL-05 | `PUT/DELETE /api/admin/colecciones/{id}/productos` | staff | Asigna/desasigna productos; `orden` opcional | 404 | UC-AD33 |
| A-COL-06 | `PATCH /api/admin/colecciones/{id}/destacada` | staff | Toggle `destacada` | 404 | UC-AD34 |

## 6. Superficie admin — pedidos, OC, stock, facturas, dashboard

### 6.1 Pedidos (kanban y máquina de estados RN-28)

| ID | Endpoint | Auth | Descripción | Errores | Refs |
| --- | --- | --- | --- | --- | --- |
| A-PED-01 | `GET /api/admin/pedidos?estado=&user_id=` | staff | Lista kanban por `estado` (columnas ↔ `pendiente/aceptado/facturado/en_logistica/entregado/rechazado`), filtro por usuario | 422 | UC-V06/V07, UC-AD12/13/14 |
| A-PED-02 | `GET /api/admin/pedidos/{id}` | staff | Detalle con líneas y datos de comprador | 404 | UC-AD12 |
| A-PED-03 | `POST /api/admin/pedidos` | staff | Crea pedido `pendiente` en nombre de un cliente | 422 | UC-V08 |
| A-PED-04 | `POST /api/admin/pedidos/{id}/aceptar` | `vendedor`/`administrador` | `pendiente → aceptado`: genera movimiento `reserva` (RN-35) y crea/associa OC (RN-19/29); 409 si stock quedaría negativo | 409/422 transición ilegal | UC-V09/AD15, TC-RN18-01 |
| A-PED-05 | `POST /api/admin/pedidos/{id}/rechazar` | `vendedor`/`administrador` | `pendiente → rechazado` (sin efecto stock) o `aceptado → rechazado` (genera `devolución`, RN-35); exige `motivo_rechazo` visible al comprador | 409/422 | UC-V10/AD16, TC-RN28-02 |
| A-PED-06 | `PATCH /api/admin/pedidos/{id}/lineas` | staff | Corrige nombre de línea / normaliza unidad o nombre (solo `pendiente`) | 409/422 | UC-AD17/18 |
| A-PED-07 | `PATCH /api/admin/pedidos/{id}/vendedor` | `administrador` | Reasigna `vendedor_id` solo en `pendiente` (RN-27); registra quién/cuándo/desde-quién | 409 | RN-27, ADR-007, TC-RN27-01 |
| A-PED-08 | `POST /api/admin/pedidos/{id}/logistica` | `administrador` | `facturado → en_logistica` (sin efecto stock); actor "Logística" no existe como rol (§9.2) | 409 | UC-AD26 |
| A-PED-09 | `POST /api/admin/pedidos/{id}/entregar` | `administrador` | `en_logistica → entregado` (terminal, sin efecto stock) | 409 | UC-AD27 |

### 6.2 Órdenes de compra y facturación (RN-29/36)

| ID | Endpoint | Auth | Descripción | Errores | Refs |
| --- | --- | --- | --- | --- | --- |
| A-OC-01 | `POST /api/admin/ordenes-compra` | staff | Consolida N `pendiente` del **mismo comprador** → 1 OC `OC-YYYY-NNNN`; todos pasan a `aceptado` juntos; totales sumados | 422 compradores mixtos / ya aceptados | UC-AD19, RN-29, TC-RN29-01/02, TC-RN18-01 |
| A-OC-02 | `GET /api/admin/ordenes-compra` | staff | Lista con estado derivado (§9.7) | — | UC-AD12 |
| A-OC-03 | `GET /api/admin/ordenes-compra/{id}` | staff | Detalle + pedidos vinculados | 404 | UC-AD12, UC-B08 (vía tienda) |
| A-OC-04 | `POST /api/admin/ordenes-compra/{id}/facturar` | `administrador` | Solo si estado derivado `aceptado` y no facturada; genera `facturas` 1:1 (`F-YYYY-NNNN`, inmutable) y todos sus pedidos pasan a `facturado` (movimiento `confirmación`, RN-35) | 409 ya facturada / estado | UC-AD25, RN-36 |
| A-STK-01 | `GET /api/admin/stock` | staff | Lista `stock` (disponible/reservada) | — | lectura staff |
| A-STK-02 | `GET /api/admin/stock/{product_id}` | staff | Detalle de stock de un producto | 404 | lectura staff |
| A-STK-03 | `GET /api/admin/stock/movimientos` | staff | Historial `movimientos_stock` (solo lectura; `ajuste_manual` fuera de MVP) | — | RN-35 |
| A-FAC-01 | `GET /api/admin/facturas` | staff | Lista `facturas` | — | RN-36 |
| A-FAC-02 | `GET /api/admin/facturas/{id}` | staff | Detalle (nunca DELETE) | 404 | RN-36 |
| A-DASH-01 | `GET /api/admin/dashboard/totales-hoy` | staff | Totales del día (RN-37): widget, no columna kanban | — | UC-AD28 |
| A-AUD-01 | `GET /api/admin/auditoria` | `administrador` | Lectura de `auditoria_staff` (filtro actor/entidad/fechas); append-only, sin borrado | 422 filtros | 02-security.md |

### 6.3 Máquina de estados ↔ endpoints

| Transición (RN-28) | Endpoint | Actor | Efecto stock (RN-35) |
| --- | --- | --- | --- |
| `pendiente → aceptado` | A-PED-04 | Vendedor/Admin | `reserva`: disponible −, reservada + |
| `pendiente → rechazado` | A-PED-05 | Vendedor/Admin | sin efecto |
| `aceptado → rechazado` | A-PED-05 | Vendedor/Admin | `devolución`: disponible +, reservada − |
| `facturado → en_logistica` | A-PED-08 | Admin (Logística: §9.2) | sin efecto |
| `en_logistica → entregado` | A-PED-09 | Admin (ídem) | sin efecto |
| consolidación N→1 OC | A-OC-01 | Admin/Vendedor | (los pedidos pasan a `aceptado`; reserva via A-PED-04 o en consolidación) |
| facturación OC | A-OC-04 | Admin | `confirmación` por línea: reservada − |

Terminales: `rechazado` (solo duplicable vía S-PED-06) y `entregado`.
Sin transiciones inversas salvo `aceptado → rechazado`.

## 7. Cobertura

### 7.1 Matriz UC → endpoints

| Actor | UCs | Endpoints |
| --- | --- | --- |
| Visitante anónimo | A01..A09, A10 | S-CAT-01..06 (A01..A08, A10 via 401/redirect de la tienda), RF-22 share fuera de API (RN-22) |
| Cuenta | C01..C10 | S-AUTH-01..05, S-CUENTA-01..04; C04 diferido (§8.2); C07 diferido (§8.4) |
| Comprador | B01..B10 | S-FAV-01..03, S-CART-01..04, S-PED-01..06, S-CAL-01..02 |
| Vendedor | V01..V11 | A-PROD-03/04, A-ETIQ-01/02, A-USR-01..06, A-PED-01/03/04/05, A-PED-02 (V11 lectura) — superficie `/api/admin` asumida, a confirmar (§8.6) |
| Administrador | AD01..AD34 | A-USR-*, A-PROD-*, A-CAT-*, A-COL-*, A-PED-*, A-OC-*, A-STK-*, A-FAC-*, A-DASH-01, A-AUD-01 |

### 7.2 Resumen RF/AUTH

- Cubiertos: RF-01..14, 16, 18..21, 23..32 (RF-09 orden `con_descuento`
  activo por ADR-008) y AUTH-01..05, 07..12.
- Diferidos: RF-15 (imagen: campo reservado, NULL en MVP), RF-17
  (recuperación), RF-28 parcial (avatar).
- Fuera de alcance: pagos, envíos/operativa logística, moderación (RN-25), seguir usuarios (RN-22).

## 8. Pendientes y diferidos

1. **Descuentos**: resuelto por ADR-008 — precio de oferta con vigencia
   (was–now) a nivel producto. Endpoints A-PROD-08/A-PROD-09 sobre
   `/api/admin`; sort `con_descuento` activo (mayor % primero, empate
   por precio efectivo ascendente); snapshot `pedido_items.precio_lista`
   para mostrar el ahorro.
2. **Recuperación de contraseña**: sin endpoint en MVP (sin email
   configurado, AUTH-06).
3. **Imágenes de producto**: campo `imagen` reservado y NULL; no hay
   endpoints de upload en MVP (RN-13).
4. **Avatar de usuario**: `users.avatar` "nulo en MVP"; UC-C07/RF-28
   quedan sin endpoint hasta decidir (§9.4).
5. **Pagos y envíos**: fuera de alcance del MVP.
6. **Superficie Vendedor**: se asume `/api/admin` (ADR-005); pendiente
   confirmación explícita (use-cases/vendedor.md).

## 9. Conflictos detectados (sin resolver aquí)

1. **UC-AD06 colisionado**: "listar/buscar/filtrar productos" y "gestionar
   árbol de categorías" comparten ID en administrador.md; este doc los
   trata como recursos separados (A-PROD-01 vs A-CAT-01..04).
2. **Actor Logística**: RN-28 habilita `facturado → en_logistica` y
   `en_logistica → entregado` para "Administrador o Logística", pero
   `users.role` no incluye ese rol. Se mapea a `administrador` (única
   lectura implementable); definir el actor queda abierto.
3. **Alcance de rechazo del Vendedor**: vendedor.md dice `* → rechazado`
   (más laxo); RN-28 solo permite rechazar desde `pendiente` y
   `aceptado`. Este doc sigue a RN-28; ajustar vendedor.md o la regla.
4. **Avatar**: RF-28/UC-C07 piden cambio de avatar; el modelo dice
   "nulo en MVP". Sin endpoint hasta decidir.
5. **Orden "con descuento"**: listado como in-scope (RN-07/RF-09) pero
   sin mecánica definida ni campo en el modelo. Criterio reservado.
   Resuelto por ADR-008 (precio de oferta con vigencia).
6. **Alias de estados**: "pendiente de validación" (RF-30/UC-B05) y las
   etiquetas kanban (Recibido/En preparación/…) son aliases de
   presentación; la API expone solo el enum almacenado de RN-28.
7. **Estado de OC derivado**: sin columna; `aceptado` = todos sus pedidos
   `aceptado`; `facturada` = EXISTS factura (1:1, `RESTRICT` tras
   facturar impide borrado). A-OC-04 valida sobre el derivado.
8. **Path de refresh admin**: ADR-003 deja el path "equivalente propio"
   sin definir; aquí se fija `Path=/api/admin/auth/refresh` (§Convenciones).
   Resuelto: implementado como `Path=/admin/auth/refresh` (A-AUTH-02).
