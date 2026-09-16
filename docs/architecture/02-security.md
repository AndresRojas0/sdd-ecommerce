# Modelo de seguridad

Autenticación, autorización y protección de datos (primera iteración).

## Autenticación

Dos sistemas **independientes** sobre el mismo backend:

| Superficie | Mecanismo | Detalle |
| ---------- | --------- | ------- |
| Tienda pública | JWT en cookies | Access 15 min + refresh rotativo 30 días; cookies `HttpOnly`, `Secure`, `SameSite=Lax`; refresh con `Path=/auth/refresh` (ADR-003). |
| Panel admin | JWT en cookies propios | Secret y audiencia distintos; credenciales iniciales por bootstrap de env (ADR-006) con cambio forzado en primer login (BOOT-03). |

- Los refresh tokens se persisten **hasheados** para permitir revocación y
  detección de reuso.
- Contraseñas: solo hash (RN-15); política mínima 8 caracteres, una
  mayúscula, un número y un caracter especial.

## Autorización (RBAC)

| Rol | Alcance |
| --- | ------- |
| Visitante anónimo | Lectura del catálogo público. |
| Comprador | Favoritos, carrito/pedidos, calificaciones sobre sus propios recursos. |
| Vendedor | Lectura de pedidos, alta de pedidos por cliente, alta de productos/etiquetas, consulta de perfiles de compradores. |
| Administrador | CRUD total + confirmación de pedidos + gestión de usuarios/roles. |

Reglas transversales: propiedad de recursos (un comprador solo ve/edita SUS
favoritos, pedidos y calificaciones), perfil de usuario privado (RN-22),
baja lógica sin borrado físico (RN-17).

## Protección de datos

- Cookies firmadas por el backend; nada sensible legible desde JS.
- Validación server-side de toda entrada (Pydantic).
- CSRF: `SameSite=Lax` + validación adicional en mutaciones sensibles.
- Secretos por variables de entorno fuera del repositorio (`.env` ignorado
  por Git).

## Rate limiting

Herramienta: **`slowapi`** (wrapper de `limits`) sobre FastAPI. Backend
in-memory en dev/nodo único; el contrato queda listo para backend Redis
si producción escala a múltiples instancias. Claves por IP y por
`user_id` cuando hay sesión.

Límites iniciales:

| Endpoint | Límite | Motivo |
| -------- | ------ | ------ |
| `login` / `refresh` | 5/min por IP | Fuerza bruta (AUTH-05). |
| `register` / `reactivar` | 3/h por IP | Abuso de alta. |
| Escritura genérica | 60/min por usuario\|IP | Protección general. |
| Lectura catálogo | 120/min por IP | Búsqueda/paginación. |
| `POST visitas` | 60/min | Además del dedup server-side (RN-08). |

Respuesta `429` con header `Retry-After` y el mismo envelope de error
de `01-api-design.md`. Healthcheck interno excluido.

## Auditoría de staff

Nueva tabla **append-only** `auditoria_staff`:

| Columna | Tipo / detalle |
| ------- | -------------- |
| `id` | PK |
| `actor_id` | FK `users` `ON DELETE SET NULL` |
| `accion` | Identificador de la acción |
| `entidad` / `entidad_id` | Entidad afectada |
| `datos_antes` / `datos_despues` | `JSONB` |
| `request_id` | Correlación con el request |
| `created_at` | `TIMESTAMPTZ` |

Alcance MVP (acciones auditadas): transiciones de pedido (aceptar,
rechazar, facturar, logística, entregar), reasignación de vendedor
(RN-27 — cubre TC-RN27-01: quién/cuándo/desde-quién va en
`datos_antes`/`datos_despues`; NO se crea la tabla `pedido_reasignaciones`
aparte que el modelo tenía como futura), toggle `is_active` de usuarios,
toggle publicación de producto, alta/baja/edición de descuento, edición
de líneas de pedido, toggle destacada de colecciones.

Sin `UPDATE` ni `DELETE`, sin endpoint de borrado; lectura vía
`GET /api/admin/auditoria` (A-AUD-01, filtrable por
actor/entidad/fechas).
