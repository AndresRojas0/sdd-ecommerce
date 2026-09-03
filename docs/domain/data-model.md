# Modelo de datos — Esquema físico PostgreSQL

> Derivado de `domain/domain-model.md` y de las reglas `RN-01`..`RN-37` (`requirements/business-rules.md`), `requirements/functional-requirements.md`, `requirements/authentication.md` y los ADR `001`, `002`, `006`, `007`. Stack: **PostgreSQL 16 · SQLAlchemy 2.0 · Alembic · Python 3.12**. Convenciones: claves primarias `UUIDv4`, tiempos `TIMESTAMPTZ`, `snake_case` en identificadores, `gen_random_uuid()` como default de PK, `now()` para marcas temporales.

## Convenciones generales

- **PK**: `UUID` (`gen_random_uuid()`, extensión `pgcrypto`). Todas las tablas usan PK `id UUID` salvo joins N:M con PK compuesta.
- **Tiempos**: `TIMESTAMPTZ NOT NULL DEFAULT now()` para `created_at`/`updated_at`; `visited_at`, `last_login_at`, `expires_at`, `deleted_at` según tabla.
- **Soft delete**: `productos.deleted_at` (`RN-32`); `users.is_active` (`RN-17`, sin `deleted_at`). Ver § Notas.
- **Borrado físico**: nunca sobre filas con historial referenciado; FK con `ON DELETE RESTRICT` salvo joins (`CASCADE`) y referencias opcionales (`SET NULL` donde se indica).
- **Mapeo ORM**: `sqlalchemy.dialects.postgresql.UUID(as_uuid=True)`, `mapped_column(..., server_default=func.gen_random_uuid())` / `func.now()`; Alembic gestiona el DDL a partir de este documento.
- **Collation**: `C` por defecto; búsquedas case-insensitive vía `ILIKE` + `pg_trgm` o `lower()` funcional donde se indexa.

## Extensiones

| Extensión | Uso | Obligatoria |
|-----------|-----|-------------|
| `pgcrypto` | `gen_random_uuid()` para PK UUIDv4 | Sí |
| `pg_trgm` | Índices `GIN (col gin_trgm_ops)` para búsqueda `ILIKE` sobre `productos.titulo`, `categorias.nombre`, `etiquetas.nombre` y autocompletado `RN-03` | Sí |
| `btree_gin` | Opcional si se combina `GIN` con btree en un mismo índice; no requerido en MVP | No |

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

## 1. `users`

Identidad por email (`RN-14`), baja lógica `is_active` (`RN-17`), bootstrap por env (`ADR-006` / `BOOT-01..04`).

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | Identificador del usuario |
| `email` | `VARCHAR(255)` | `UNIQUE NOT NULL` | Identidad única, clave de login (`RN-14`) |
| `display_name` | `VARCHAR(100)` | `NOT NULL` | Nombre visible |
| `avatar` | `VARCHAR(500)` | `NULL` | URL de imagen de perfil; nulo en MVP |
| `password_hash` | `VARCHAR(255)` | `NOT NULL` | Hash (nunca texto plano, `RN-15`) |
| `is_active` | `BOOLEAN` | `NOT NULL DEFAULT true` | Baja lógica; `false` = dado de baja (`RN-17`) |
| `must_change_password` | `BOOLEAN` | `NOT NULL DEFAULT false` | `true` fuerza cambio en primer login (`BOOT-03`) |
| `role` | `VARCHAR(20)` | `NOT NULL DEFAULT 'comprador' CHECK (role IN ('comprador','vendedor','administrador'))` | Rol de autorización |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Fecha de creación del perfil |
| `last_login_at` | `TIMESTAMPTZ` | `NULL` | Último login exitoso |

> Sin `deleted_at`: la baja lógica se resuelve con `is_active` (`RN-17`, `ADR-002`). La reactivación nativa conserva el mismo `id` y todo el historial.

Índices: `UNIQUE (email)`, `idx_users_email` (btree), `idx_users_role`, `idx_users_is_active`.

Seed/bootstrap: ver § Bootstrap `users` al final.

## 2. `categorias`

Taxonomía cerrada (`RN-01`). Color del badge.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | PK |
| `nombre` | `VARCHAR(100)` | `UNIQUE NOT NULL` | Nombre de la categoría |
| `slug` | `VARCHAR(120)` | `UNIQUE NOT NULL` | Slug SEO (`RN-20`) |
| `color` | `VARCHAR(7)` | `NOT NULL CHECK (color ~ '^#[0-9A-Fa-f]{6}$')` | Hex del badge, ej. `#003087` |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Alta |

Índices: `UNIQUE (slug)`, `idx_categorias_slug`, `UNIQUE (nombre)`.

Seed: `bazar`, `calefacción`, `cerrajería`, `construcción`, `corte`, `desbaste y pulido`, `electricidad`, `fontanería`, `iluminación`, `gas`, `herramientas`, `materias primas`, `pintura`, `plomería`, `refrigeración`, `sanitarios`, `suministros seguridad` (`RN-01`).

## 3. `etiquetas`

Vocabulario abierto (`RN-02`), autocompletado por substring (`RN-03`).

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | PK |
| `nombre` | `VARCHAR(100)` | `UNIQUE NOT NULL` | Término, ej. `inoxidable` |
| `slug` | `VARCHAR(120)` | `UNIQUE NOT NULL` | Slug SEO (`RN-20`) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Alta |

Índices: `UNIQUE (slug)`, `idx_etiquetas_slug`, `idx_etiquetas_nombre_trgm GIN (nombre gin_trgm_ops)` para `ILIKE '%tor%'`.

Seed: `accesorio`, `acero`, `aluminio`, `bronce`, `cable`, `cobre`, `disco`, `hexagonal`, `inoxidable`, `llave`, `madera`, `metal`, `plástico`, `repuesto`, `tornillos`, `tuerca`, etc.

## 4. `unidades_medida`

Registro abierto y extensible (`RN-23`). Sin rediseño para nuevas unidades.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | PK |
| `nombre` | `VARCHAR(50)` | `UNIQUE NOT NULL` | Ej. `unidades`, `cm`, `m`, `kg` |
| `simbolo` | `VARCHAR(10)` | `NOT NULL` | Símbolo corto, ej. `u`, `cm`, `m`, `kg` |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Alta |

Índices: `UNIQUE (nombre)`.

Seed obligatorio (`RN-23`): `unidades`, `cm`, `m`, `kg` (al menos).

## 5. `productos`

Entidad central. Precio obligatorio (`RN-11`), imagen nullable (`RN-13`), unidad de venta (`RN-23`), publicación/oculto (`RN-31`), borrado lógico (`RN-32`), contadores cacheados (`RN-08`/`RN-09`/`RN-30`/`RN-21`). Stock **no** vive en esta tabla; ver `stock` (RN-35, §16).

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | PK |
| `titulo` | `VARCHAR(200)` | `NOT NULL` | Nombre del producto |
| `slug` | `VARCHAR(220)` | `UNIQUE NOT NULL` | Slug SEO (`RN-20`) |
| `descripcion` | `TEXT` | `NULL` | Descripción larga |
| `componentes_incluidos` | `TEXT` | `NULL` | Lista de componentes |
| `datos_tecnicos` | `JSONB` | `NULL DEFAULT '{}'::jsonb` | Especificaciones buscables (`RN-04`) |
| `precio` | `NUMERIC(10,2)` | `NOT NULL CHECK (precio > 0)` | Precio unitario (`RN-11`) |
| `imagen` | `VARCHAR(500)` | `NULL` | URL imagen; nulo en MVP (`RN-13`) |
| `unidad_venta_id` | `UUID` | `FK -> unidades_medida.id NOT NULL ON DELETE RESTRICT` | Unidad de venta (`RN-23`) |
| `estado_publicacion` | `VARCHAR(20)` | `NOT NULL DEFAULT 'publicado' CHECK (estado_publicacion IN ('publicado','oculto'))` | Visibilidad (`RN-31`) |
| `deleted_at` | `TIMESTAMPTZ` | `NULL` | Borrado lógico; no NULL = eliminado (`RN-32`) |
| `visitas_count` | `INTEGER` | `NOT NULL DEFAULT 0 CHECK (visitas_count >= 0)` | Cache contador visitas (`RN-08`) |
| `guardados_count` | `INTEGER` | `NOT NULL DEFAULT 0 CHECK (guardados_count >= 0)` | Cache guardados (`RN-09`) |
| `busquedas_count` | `INTEGER` | `NOT NULL DEFAULT 0 CHECK (busquedas_count >= 0)` | Relevancia (`RN-30`) |
| `calificacion_promedio` | `NUMERIC(3,2)` | `NOT NULL DEFAULT 0 CHECK (calificacion_promedio BETWEEN 0 AND 5)` | Promedio `Σ/cantidad` (`RN-21`) |
| `calificacion_cantidad` | `INTEGER` | `NOT NULL DEFAULT 0 CHECK (calificacion_cantidad >= 0)` | Cantidad de calificaciones |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Alta |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Última edición (trigger) |

Índices:

- `UNIQUE (slug)` + `idx_productos_slug`
- `idx_productos_estado_publicacion` (`estado_publicacion`) — filtro catálogo público vs staff (`RN-31`)
- `idx_productos_deleted_at` — excluye borrados lógicos en queries públicas
- `idx_productos_precio` (btree) — ordenamientos precio (`RN-07`)
- `idx_productos_created_at` (btree DESC) — `más reciente` (`RN-07`)
- `idx_productos_titulo_trgm GIN (titulo gin_trgm_ops)` — búsqueda por nombre (`RN-04`)
- `idx_productos_datos_tecnicos_gin GIN (datos_tecnicos)` — búsqueda en specs (`RN-04`)
- Parcial recomendado: `CREATE INDEX idx_productos_publicos ON productos (created_at) WHERE deleted_at IS NULL AND estado_publicacion='publicado'`

Trigger: `updated_at = now()` en `UPDATE`.

## 6. `producto_categorias` (N:M)

`RN-01`: un producto pertenece a una o más categorías.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `product_id` | `UUID` | `PK, FK -> productos.id ON DELETE CASCADE NOT NULL` | Producto |
| `categoria_id` | `UUID` | `PK, FK -> categorias.id ON DELETE RESTRICT NOT NULL` | Categoría |

PK compuesta `(product_id, categoria_id)`. Índices: `idx_pc_product_id`, `idx_pc_categoria_id`. Check de aplicación: al crear producto exigir `COUNT(categoria_id) >= 1`.

## 7. `producto_etiquetas` (N:M)

`RN-02`: cero o más etiquetas por producto.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `product_id` | `UUID` | `PK, FK -> productos.id ON DELETE CASCADE NOT NULL` | Producto |
| `etiqueta_id` | `UUID` | `PK, FK -> etiquetas.id ON DELETE RESTRICT NOT NULL` | Etiqueta |

PK compuesta `(product_id, etiqueta_id)`. Índices: `idx_pt_product_id`, `idx_pt_etiqueta_id`.

## 8. `favoritos`

`RN-09`: incrementa/decrementa `productos.guardados_count`.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | PK |
| `user_id` | `UUID` | `FK -> users.id ON DELETE CASCADE NOT NULL` | Usuario que guarda (`RN-06` requiere auth) |
| `product_id` | `UUID` | `FK -> productos.id ON DELETE CASCADE NOT NULL` | Producto guardado |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Fecha de guardado |

Restricciones: `UNIQUE (user_id, product_id)`. Índices: `idx_favoritos_user_id`, `idx_favoritos_product_id`. Comportamiento: `INSERT` → `guardados_count+1`; `DELETE` → `guardados_count-1` con piso `0` (transacción + `CHECK`).

## 9. `visitas`

`RN-08` + `ADR-001`: deduplicación por visitante y ventana configurable (`VISIT_DEDUP_WINDOW_HOURS`, default 24h); origen para `RN-30`.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | PK |
| `product_id` | `UUID` | `FK -> productos.id ON DELETE CASCADE NOT NULL` | Producto visitado |
| `user_id` | `UUID` | `FK -> users.id ON DELETE SET NULL NULL` | Visitante autenticado; NULL si anónimo |
| `visitor_cookie` | `VARCHAR(100)` | `NULL` | UUID cookie anónima (`ADR-001`); NULL si autenticado |
| `visited_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Momento de la visita |
| `origen` | `VARCHAR(20)` | `NOT NULL DEFAULT 'directa' CHECK (origen IN ('directa','busqueda'))` | Origen para relevancia (`RN-30`) |

Restricciones: `CHECK (user_id IS NOT NULL OR visitor_cookie IS NOT NULL)` — al menos un identificador.

Índices:

- `idx_visitas_product_visited (product_id, visited_at DESC)` — agregaciones y listados
- `idx_visitas_user_product_time (product_id, user_id, visited_at)` — dedup autenticado
- `idx_visitas_cookie_product_time (product_id, visitor_cookie, visited_at)` — dedup anónimo
- Parcial para ventana: `WHERE visited_at > now() - interval`

Dedup: lógica de aplicación `SELECT 1 FROM visitas WHERE product_id=$1 AND (user_id=$2 OR visitor_cookie=$3) AND visited_at > now() - interval 'X hours'`. Solo si no existe fila, `INSERT` y `UPDATE productos SET visitas_count = visitas_count+1` (y `busquedas_count+1` si `origen='busqueda'`).

## 10. `calificaciones`

`RN-21` (promedio fraccional), `RN-33` (elegibilidad), `TC-RN33-*`.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | PK |
| `user_id` | `UUID` | `FK -> users.id ON DELETE CASCADE NOT NULL` | Autor |
| `product_id` | `UUID` | `FK -> productos.id ON DELETE CASCADE NOT NULL` | Producto calificado |
| `estrellas` | `SMALLINT` | `NOT NULL CHECK (estrellas BETWEEN 1 AND 5)` | 1..5 (`RN-21`) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Alta |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Última edición (trigger) |

Restricciones: `UNIQUE (user_id, product_id)` — una calificación por usuario/producto, editable. Índices: `idx_calificaciones_product_id`, `idx_calificaciones_user_id`.

Elegibilidad (`RN-33`): check de aplicación — existe `pedidos` con `estado='aceptado'` y `pedido_items.product_id = calificaciones.product_id` y `pedidos.user_id = calificaciones.user_id`. No es FK/CHECK por depender de estado de otro agregado.

Mantenimiento de promedio: transacción que recalcula `productos.calificacion_promedio` y `calificacion_cantidad` tras `INSERT/UPDATE/DELETE` (o trigger `AFTER`).

## 11. `carritos`

`RN-34`: server-side, un carrito activo por usuario, sobrevive logout/cambio de dispositivo.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | PK |
| `user_id` | `UUID` | `FK -> users.id ON DELETE CASCADE UNIQUE NOT NULL` | Dueño; `UNIQUE` impone 1 carrito/usuario |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Alta |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Última modificación (trigger) |

Índice: `UNIQUE (user_id)` (`idx_carritos_user_id`).

Visitante anónimo no tiene carrito: el UI dispara prompt de login (`RN-34`).

## 12. `carrito_items`

Líneas del carrito. Cantidad fraccional para `kg`/`m` (`RN-23`). Precio snapshot al momento de agregar.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | PK |
| `carrito_id` | `UUID` | `FK -> carritos.id ON DELETE CASCADE NOT NULL` | Carrito |
| `product_id` | `UUID` | `FK -> productos.id ON DELETE RESTRICT NOT NULL` | Producto |
| `cantidad` | `NUMERIC(10,2)` | `NOT NULL CHECK (cantidad > 0)` | Cantidad en unidad de venta del producto |
| `precio_unitario` | `NUMERIC(10,2)` | `NOT NULL CHECK (precio_unitario > 0)` | Snapshot de `productos.precio` |
| `subtotal` | `NUMERIC(12,2)` | `NOT NULL CHECK (subtotal >= 0)` | `cantidad * precio_unitario` (aplicación o `GENERATED ALWAYS AS (cantidad * precio_unitario) STORED`) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Alta |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Edición |

Restricciones: `UNIQUE (carrito_id, product_id)` — un renglón por producto. Índices: `idx_carrito_items_carrito_id`, `idx_carrito_items_product_id`.

## 13. `pedidos`

`RN-26` (atributos mínimos), `RN-28` (máquina extendida), `RN-27`/`ADR-007` (reasignación), `RN-29` (consolidación N:1), `RN-18`/`RN-19`, `RN-35` (stock), `RN-36` (factura vía OC).

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | PK |
| `user_id` | `UUID` | `FK -> users.id ON DELETE RESTRICT NOT NULL` | Cliente creador (`RN-26`); `RESTRICT` preserva historial |
| `vendedor_id` | `UUID` | `FK -> users.id ON DELETE SET NULL NULL` | Vendedor asignado; NULL hasta asignar; reasignable si `pendiente` (`RN-27`) |
| `estado` | `VARCHAR(30)` | `NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente','aceptado','facturado','en_logistica','entregado','rechazado'))` | Estado — máquina extendida (`RN-28`): `pendiente → aceptado → facturado → en_logistica → entregado`, más `rechazado` terminal |
| `motivo_rechazo` | `TEXT` | `NULL CHECK (motivo_rechazo IS NULL OR estado='rechazado')` | Motivo si rechazado (`RN-28`) |
| `subtotal` | `NUMERIC(12,2)` | `NOT NULL CHECK (subtotal >= 0)` | Suma de `pedido_items.subtotal` |
| `total` | `NUMERIC(12,2)` | `NOT NULL CHECK (total >= 0)` | Total (igual a subtotal en MVP; reserva descuentos) |
| `orden_compra_id` | `UUID` | `FK -> ordenes_compra.id ON DELETE SET NULL NULL` | OC que lo consolida (`RN-29`); NULL si no consolidado |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Fecha creación (`RN-26`) |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Última transición |

Índices: `idx_pedidos_user_id`, `idx_pedidos_vendedor_id`, `idx_pedidos_estado`, `idx_pedidos_orden_compra_id`, `idx_pedidos_created_at DESC`, `idx_pedidos_user_estado (user_id, estado)`.

Reglas de aplicación (no CHECK simples):

- Solo `pendiente` es editable/eliminable por su `user_id`; `DELETE` físico solo si `pendiente`; `rechazado`/`entregado` son terminales (`RN-28`, `TC-RN28-01`).
- `rechazado` solo admite duplicación como nuevo `pendiente` con `motivo_rechazo` visible.
- Reasignación `vendedor_id` solo si `estado='pendiente'` y por `role='administrador'` con auditoría (`RN-27`, `TC-RN27-01`).
- Consolidación (`RN-29`): solo `pendiente`, mismo `user_id`, todos pasan a `aceptado` juntos al crear la OC; luego avanzan juntos a `facturado` al facturar la OC (RN-36).
- Transiciones de estado (`RN-28`): `pendiente → aceptado` (Vendedor/Admin, reserva RN-35), `pendiente → rechazado` (Vendedor/Admin), `aceptado → facturado` (solo Admin, confirmación RN-35 + Factura RN-36), `aceptado → rechazado` (Vendedor/Admin, devolución RN-35), `facturado → en_logistica` (Admin/Logística), `en_logistica → entregado` (Admin/Logística). Validación en servicio con `409/422` si transición ilegal o actor no autorizado.
- Efectos stock (RN-35) se ejecutan en la misma transacción que el cambio de estado; ver §16 `stock` / `movimientos_stock`.

## 14. `pedido_items`

Líneas del pedido (`RN-26`). Snapshot de precio.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | PK |
| `pedido_id` | `UUID` | `FK -> pedidos.id ON DELETE CASCADE NOT NULL` | Pedido |
| `product_id` | `UUID` | `FK -> productos.id ON DELETE RESTRICT NOT NULL` | Producto (`RESTRICT` protege historial si producto está `deleted_at`) |
| `cantidad` | `NUMERIC(10,2)` | `NOT NULL CHECK (cantidad > 0)` | Cantidad en unidad de venta |
| `precio_unitario` | `NUMERIC(10,2)` | `NOT NULL CHECK (precio_unitario > 0)` | Snapshot al confirmar |
| `subtotal` | `NUMERIC(12,2)` | `NOT NULL CHECK (subtotal >= 0)` | `cantidad * precio_unitario` |

Índices: `idx_pedido_items_pedido_id`, `idx_pedido_items_product_id`. `UNIQUE` no se impone: un mismo producto podría aparecer en líneas distintas si se duplica un pedido rechazado con ediciones; la unicidad se deja a la capa de carrito.

## 15. `ordenes_compra`

Documento comercial (`RN-18`, `RN-29`). N pedidos → 1 OC. `RN-27`: OC congelada con atribución original. Unidad facturable para `facturas` (RN-36): 1 OC → 1 Factura.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | PK |
| `numero` | `VARCHAR(30)` | `UNIQUE NOT NULL` | Humano-legible, ej. `OC-2026-0001` (secuencia) |
| `total` | `NUMERIC(12,2)` | `NOT NULL CHECK (total >= 0)` | Suma de totales de pedidos vinculados |
| `created_by` | `UUID` | `FK -> users.id ON DELETE SET NULL NULL` | Admin/Vendedor que confirmó (`RN-18`) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Emisión |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Correcciones administrativas |

Índices: `UNIQUE (numero)`, `idx_oc_created_at`, `idx_oc_created_by`.

Secuencia para `numero`: `SEQUENCE oc_numero_seq` o función `nextval` + formateo `OC-YYYY-NNNN` en aplicación; alternativa `GENERATED` con trigger `BEFORE INSERT`.

Relación: `pedidos.orden_compra_id -> ordenes_compra.id` (N:1). No hay tabla de join adicional. `facturas.orden_compra_id -> ordenes_compra.id` (1:1, RN-36) completa el triángulo `pedidos N — 1 ordenes_compra 1 — 1 facturas`.

## 16. `stock` y `movimientos_stock` (RN-35)

Stock físico por producto. Separado de `productos` para no mezclar catálogo con disponibilidad. Un producto sin fila en `stock` se considera sin stock inicial (se crea con ceros al dar de alta el producto o por migración).

### 16.1 `stock`

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `product_id` | `UUID` | `PK, FK -> productos.id ON DELETE CASCADE NOT NULL` | Producto (PK y FK, relación 1:1) |
| `cantidad_disponible` | `NUMERIC(10,2)` | `NOT NULL DEFAULT 0 CHECK (cantidad_disponible >= 0)` | Unidades libres para vender |
| `cantidad_reservada` | `NUMERIC(10,2)` | `NOT NULL DEFAULT 0 CHECK (cantidad_reservada >= 0)` | Unidades comprometidas por pedidos `aceptado` aún no facturados |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Último movimiento (trigger) |

Índices: `PK (product_id)` es el único índice necesario; `FK` indexado implícitamente. Trigger: `updated_at = now()` en `UPDATE`.

Invariantes (aplicación + CHECK):

- `cantidad_disponible >= 0`, `cantidad_reservada >= 0` siempre.
- `aceptado` (reserva): `disponible -= Σ pedido_items.cantidad`, `reservada += Σ cantidad`; falla si `disponible` quedaría negativa (validar antes de transicionar; `409 Conflict` si sin stock).
- `facturado` (confirmación): `reservada -= Σ cantidad`; `disponible` no cambia (ya se descontó al reservar).
- `aceptado → rechazado` (devolución): `disponible += Σ cantidad`, `reservada -= Σ cantidad`.

### 16.2 `movimientos_stock`

Historial auditable de cada cambio de stock. Un movimiento por transición que afecta stock.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | PK |
| `product_id` | `UUID` | `FK -> productos.id ON DELETE CASCADE NOT NULL` | Producto afectado |
| `tipo` | `VARCHAR(20)` | `NOT NULL CHECK (tipo IN ('reserva','confirmacion','devolucion'))` | Tipo de movimiento (RN-35) |
| `cantidad` | `NUMERIC(10,2)` | `NOT NULL CHECK (cantidad > 0)` | Cantidad movida (positiva; el signo lo da el tipo) |
| `pedido_id` | `UUID` | `FK -> pedidos.id ON DELETE SET NULL NULL` | Pedido origen; `SET NULL` si el pedido pendiente se elimina |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Momento del movimiento |

Índices: `idx_mov_stock_product_id (product_id)`, `idx_mov_stock_pedido_id (pedido_id)`, `idx_mov_stock_created_at (created_at DESC)`, `idx_mov_stock_product_tipo (product_id, tipo)`.

Notas:

- `reserva` y `devolucion` son inversos; `confirmacion` solo decrementa `reservada`.
- La cantidad se registra por producto; un pedido con N líneas genera N filas (una por `pedido_items.product_id`).
- No hay `ajuste_manual` en MVP; se incorporará si el negocio requiere correcciones de inventario.

## 17. `facturas` (RN-36, RN-37)

Documento fiscal emitido desde una orden de compra aceptada. 1:1 con `ordenes_compra`.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | PK |
| `orden_compra_id` | `UUID` | `FK -> ordenes_compra.id ON DELETE RESTRICT UNIQUE NOT NULL` | OC origen (UNIQUE impone 1:1); `RESTRICT` impide borrar OC facturada |
| `numero_fiscal` | `VARCHAR(30)` | `UNIQUE NOT NULL` | Número fiscal único e inmutable, ej. `F-2026-0001` (secuencia) |
| `total` | `NUMERIC(12,2)` | `NOT NULL CHECK (total >= 0)` | Total facturado (snapshot de `ordenes_compra.total` al facturar) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Fecha de emisión (para totales del día RN-37) |
| `created_by` | `UUID` | `FK -> users.id ON DELETE SET NULL NULL` | Admin que facturó |

Índices: `UNIQUE (orden_compra_id)`, `UNIQUE (numero_fiscal)`, `idx_facturas_created_at (created_at)`, `idx_facturas_created_by`.

Secuencia para `numero_fiscal`: `SEQUENCE factura_numero_seq` + formateo `F-YYYY-NNNN` en aplicación o trigger `BEFORE INSERT` (análogo a `ordenes_compra.numero`).

Reglas de aplicación:

- Solo facturable si la OC existe y todos sus pedidos están en `aceptado` (o ya `facturado` tras la operación) y no existe factura previa para esa OC (`UNIQUE` lo garantiza a nivel físico).
- `numero_fiscal` se asigna una vez y no se reedita.
- Totales del día (RN-37): `SELECT COALESCE(SUM(total),0) FROM facturas WHERE created_at::date = CURRENT_DATE` (o `created_at >= date_trunc('day', now())`). Widget de dashboard, no columna kanban.

## 18. `refresh_tokens`

`ADR-003`: refresh rotativo, familia para detección de reuso, persistencia hasheada.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | PK |
| `user_id` | `UUID` | `FK -> users.id ON DELETE CASCADE NOT NULL` | Propietario |
| `token_hash` | `VARCHAR(255)` | `UNIQUE NOT NULL` | SHA-256 del token (nunca token plano) |
| `family_id` | `UUID` | `NOT NULL` | Familia de rotación; reuso de token viejo invalida toda la familia |
| `expires_at` | `TIMESTAMPTZ` | `NOT NULL` | Expiración (30 días desde emisión) |
| `revoked` | `BOOLEAN` | `NOT NULL DEFAULT false` | Revocado explícitamente (logout / cambio de contraseña) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` | Emisión |

Índices: `UNIQUE (token_hash)`, `idx_rt_user_id`, `idx_rt_family_id`, `idx_rt_expires_at`. Expiración limpia por job o `DELETE WHERE expires_at < now()`.

Rotación: en `POST /auth/refresh` se revoca el token presentado (`revoked=true`), se emite nuevo token con mismo `family_id`; si llega un token ya revocado de esa familia → revocar toda la familia (`UPDATE ... SET revoked=true WHERE family_id=$1`).

Cambio de contraseña (`RF-29`): `UPDATE refresh_tokens SET revoked=true WHERE user_id=$1`.

> Dos audiencias aisladas (tienda vs admin, `ADR-003`/`ADR-005`) comparten el mismo esquema físico; la separación es por `aud`/`scope` en el JWT y por nombres de cookie/secretos distintos en la capa de aplicación, no por tablas separadas.

## 19. `alembic_version`

Tabla creada automáticamente por Alembic. No modelar en ORM.

| Columna | Tipo | Restricciones |
|---------|------|---------------|
| `version_num` | `VARCHAR(32)` | `PK NOT NULL` |

## Resumen de índices

| Tabla | Índice | Columnas | Tipo | Propósito |
|-------|--------|----------|------|-----------|
| `users` | `idx_users_email` | `email` | btree unique | Login (`AUTH-03`) |
| `users` | `idx_users_role` | `role` | btree | Filtro por rol |
| `users` | `idx_users_is_active` | `is_active` | btree | Baja lógica |
| `categorias` | `idx_categorias_slug` | `slug` | btree unique | SEO (`RN-20`) |
| `etiquetas` | `idx_etiquetas_slug` | `slug` | btree unique | SEO |
| `etiquetas` | `idx_etiquetas_nombre_trgm` | `nombre` | GIN trgm | Autocompletado (`RN-03`) |
| `productos` | `idx_productos_slug` | `slug` | btree unique | SEO |
| `productos` | `idx_productos_estado_publicacion` | `estado_publicacion` | btree | `RN-31` |
| `productos` | `idx_productos_deleted_at` | `deleted_at` | btree | `RN-32` |
| `productos` | `idx_productos_precio` | `precio` | btree | Orden precio (`RN-07`) |
| `productos` | `idx_productos_created_at` | `created_at DESC` | btree | Más reciente (`RN-07`) |
| `productos` | `idx_productos_titulo_trgm` | `titulo` | GIN trgm | Búsqueda (`RN-04`) |
| `productos` | `idx_productos_datos_tecnicos_gin` | `datos_tecnicos` | GIN jsonb | Búsqueda specs (`RN-04`) |
| `producto_categorias` | `idx_pc_product_id` | `product_id` | btree | Join |
| `producto_categorias` | `idx_pc_categoria_id` | `categoria_id` | btree | Join inverso |
| `producto_etiquetas` | `idx_pt_product_id` | `product_id` | btree | Join |
| `producto_etiquetas` | `idx_pt_etiqueta_id` | `etiqueta_id` | btree | Join inverso |
| `favoritos` | `idx_favoritos_user_id` | `user_id` | btree | Listado por usuario |
| `favoritos` | `idx_favoritos_product_id` | `product_id` | btree | Contador |
| `visitas` | `idx_visitas_product_visited` | `product_id, visited_at` | btree | Agregación |
| `visitas` | `idx_visitas_user_product_time` | `product_id, user_id, visited_at` | btree | Dedup auth |
| `visitas` | `idx_visitas_cookie_product_time` | `product_id, visitor_cookie, visited_at` | btree | Dedup anónimo |
| `calificaciones` | `idx_calificaciones_product_id` | `product_id` | btree | Promedio (`RN-21`) |
| `carritos` | `idx_carritos_user_id` | `user_id` | btree unique | 1 carrito/usuario (`RN-34`) |
| `carrito_items` | `idx_carrito_items_carrito_id` | `carrito_id` | btree | Listado |
| `pedidos` | `idx_pedidos_user_id` | `user_id` | btree | Pedidos por cliente |
| `pedidos` | `idx_pedidos_vendedor_id` | `vendedor_id` | btree | Asignación (`RN-27`) |
| `pedidos` | `idx_pedidos_estado` | `estado` | btree | Filtro estado |
| `pedidos` | `idx_pedidos_orden_compra_id` | `orden_compra_id` | btree | Consolidación (`RN-29`) |
| `pedido_items` | `idx_pedido_items_pedido_id` | `pedido_id` | btree | Líneas |
| `ordenes_compra` | `idx_oc_created_at` | `created_at` | btree | Listado cronológico |
| `stock` | `stock_pkey` | `product_id` | btree PK | Stock 1:1 (`RN-35`) |
| `movimientos_stock` | `idx_mov_stock_product_id` | `product_id` | btree | Historial stock (`RN-35`) |
| `movimientos_stock` | `idx_mov_stock_pedido_id` | `pedido_id` | btree | Trazabilidad pedido |
| `movimientos_stock` | `idx_mov_stock_created_at` | `created_at DESC` | btree | Auditoría |
| `facturas` | `idx_facturas_created_at` | `created_at` | btree | Totales día (`RN-37`) |
| `facturas` | `idx_facturas_numero_fiscal` | `numero_fiscal` | btree unique | Fiscal (`RN-36`) |
| `facturas` | `idx_facturas_orden_compra_id` | `orden_compra_id` | btree unique | 1:1 OC (`RN-36`) |
| `refresh_tokens` | `idx_rt_family_id` | `family_id` | btree | Detección reuso |
| `refresh_tokens` | `idx_rt_token_hash` | `token_hash` | btree unique | Lookup |

Índices parciales recomendados (creación opcional tras medir):

```sql
CREATE INDEX idx_productos_publicos ON productos (created_at DESC)
  WHERE deleted_at IS NULL AND estado_publicacion = 'publicado';
CREATE INDEX idx_visitas_recientes ON visitas (product_id, visited_at DESC)
  WHERE visited_at > now() - interval '30 days';
```

## Restricciones y mapeo a RN / AUTH / BOOT

| Restricción | Tabla(s) | Regla | Notas |
|-------------|----------|-------|-------|
| `CHECK role IN (...)` | `users` | `AUTH-03` | Roles del sistema |
| `UNIQUE email` | `users` | `RN-14` | Identidad por email |
| `is_active` sin `deleted_at` | `users` | `RN-17`, `ADR-002` | Baja lógica conserva `id` |
| `must_change_password` | `users` | `BOOT-03` | Forzado en primer login |
| `CHECK color ~ '^#[0-9A-Fa-f]{6}$'` | `categorias` | Dominio | Badge |
| `FK producto_categorias` + app check `>=1` | `productos` | `RN-01` | Al menos una categoría |
| `GIN trgm` en `etiquetas.nombre` | `etiquetas` | `RN-03` | Autocompletado `ILIKE '%...%'` |
| `FK unidad_venta_id RESTRICT` | `productos` | `RN-23` | Unidad del registro abierto |
| `CHECK precio > 0` | `productos`, `carrito_items`, `pedido_items` | `RN-11` | Precio obligatorio |
| `CHECK estado_publicacion` | `productos` | `RN-31` | Ocultar/despublicar |
| `deleted_at IS NULL` filtro | `productos` | `RN-32` | Borrado lógico |
| `GIN datos_tecnicos` + `GIN trgm titulo` | `productos` | `RN-04` | Búsqueda combinable |
| `UNIQUE (user_id, product_id)` | `favoritos` | `RN-09` | Guardado idempotente |
| `CHECK guardados_count >=0` | `productos` | `RN-09` | Piso cero |
| `CHECK (user_id OR visitor_cookie)` | `visitas` | `ADR-001` | Identificación visitante |
| `origen IN ('directa','busqueda')` | `visitas` | `RN-30` | Relevancia |
| Ventana dedup `VISIT_DEDUP_WINDOW_HOURS` | `visitas` (app) | `RN-08` | F5 no cuenta |
| `UNIQUE (user_id, product_id)` | `calificaciones` | `RN-21` | Una por usuario/producto |
| `CHECK estrellas 1..5` | `calificaciones` | `RN-21` | Rango |
| Elegibilidad por `pedido aceptado` | `calificaciones` (app) | `RN-33` | `EXISTS` sobre `pedidos` |
| `UNIQUE user_id` | `carritos` | `RN-34` | Un carrito por usuario |
| `UNIQUE (carrito_id, product_id)` | `carrito_items` | `RN-12` | Una línea por producto en carrito |
| `CHECK cantidad > 0` (`NUMERIC(10,2)`) | `carrito_items`, `pedido_items` | `RN-23` | Fraccional para `kg`/`m` |
| `CHECK estado IN (...)` | `pedidos` | `RN-28` | Máquina extendida `pendiente/aceptado/facturado/en_logistica/entregado/rechazado` |
| `CHECK motivo_rechazo` solo si `rechazado` | `pedidos` | `RN-28` | Motivo visible |
| `FK vendedor_id SET NULL` | `pedidos` | `RN-27`, `ADR-007` | Reasignable si pendiente |
| `FK orden_compra_id SET NULL` | `pedidos` | `RN-29` | Consolidación N:1; facturación vía OC (RN-36) |
| Solo `pendiente` editable/eliminable | `pedidos` (app) | `RN-28` | `409/422` si no |
| Transiciones extendidas + actor | `pedidos` (app) | `RN-28` | `pendiente→aceptado` (Vend/Admin), `→facturado` (Admin), `→en_logistica/entregado` (Admin/Logística) |
| `CHECK cantidad_disponible/reservada >=0` | `stock` | `RN-35` | Piso cero stock |
| `PK product_id FK` 1:1 | `stock` | `RN-35` | Un stock por producto |
| `CHECK tipo IN (...)` | `movimientos_stock` | `RN-35` | `reserva/confirmacion/devolucion` |
| `FK pedido_id SET NULL` | `movimientos_stock` | `RN-35` | Trazabilidad |
| `UNIQUE orden_compra_id` + `RESTRICT` | `facturas` | `RN-36` | 1 factura por OC; OC facturada no borrable |
| `UNIQUE numero_fiscal` | `facturas` | `RN-36` | Fiscal único e inmutable |
| Totales del día (widget) | `facturas` (app) | `RN-37` | `SUM(total) WHERE created_at::date = CURRENT_DATE` |
| Validación `password_hash` política | `users` (app) | `RN-15` | Hash + validación previa |
| `UNIQUE token_hash`, `family_id` | `refresh_tokens` | `ADR-003` | Rotación y reuso |
| `revoked` en cambio de contraseña | `refresh_tokens` (app) | `RF-29` | Invalida sesiones |
| `UNIQUE numero` | `ordenes_compra` | `RN-29` | `OC-YYYY-NNNN` |
| `ON DELETE CASCADE` en joins | `producto_*`, `favoritos`, `calificaciones`, `stock`, `movimientos_stock` | Integridad | Limpieza huérfanos |
| `ON DELETE RESTRICT` en históricos | `pedido_items.product_id`, `pedidos.user_id`, `facturas.orden_compra_id` | `RN-32`, `RN-19`, `RN-36` | Preserva documentos |

Validaciones que **no** son `CHECK`/`FK` y viven en aplicación (documentadas como tal): ventana de dedup de visitas, elegibilidad `RN-33`, máquina de estados extendida `RN-28` (+ validación de actor por transición), consolidación mismo comprador `RN-29`, reasignación `RN-27`, movimientos de stock `RN-35` (disponibilidad negativa), facturación `RN-36` (OC ya facturada), totales del día `RN-37` (agregación), concatenación de búsquedas con filtros `RN-04`/`RN-05`.

## Diagrama ER

```mermaid
erDiagram
    users ||--o{ favoritos : marca
    users ||--o{ calificaciones : emite
    users ||--o{ visitas : genera
    users ||--o| carritos : posee
    users ||--o{ pedidos : "crea (cliente)"
    users ||--o{ pedidos : "asigna (vendedor)"
    users ||--o{ ordenes_compra : confirma
    users ||--o{ facturas : factura
    users ||--o{ refresh_tokens : autentica

    productos ||--o{ producto_categorias : pertenece
    categorias ||--o{ producto_categorias : agrupa
    productos ||--o{ producto_etiquetas : etiqueta
    etiquetas ||--o{ producto_etiquetas : describe
    unidades_medida ||--o{ productos : define_venta

    productos ||--o| stock : tiene
    productos ||--o{ movimientos_stock : historial
    productos ||--o{ favoritos : es_guardado
    productos ||--o{ visitas : es_visitado
    productos ||--o{ calificaciones : es_calificado
    productos ||--o{ carrito_items : en_carrito
    productos ||--o{ pedido_items : en_pedido

    pedidos ||--o{ movimientos_stock : origina
    carritos ||--o{ carrito_items : contiene
    pedidos ||--o{ pedido_items : contiene
    ordenes_compra ||--o{ pedidos : consolida
    ordenes_compra ||--o| facturas : genera

    producto_categorias {
        uuid product_id PK_FK
        uuid categoria_id PK_FK
    }
    producto_etiquetas {
        uuid product_id PK_FK
        uuid etiqueta_id PK_FK
    }
    productos {
        uuid id PK
        string slug UK
        numeric precio
        uuid unidad_venta_id FK
        string estado_publicacion
        timestamptz deleted_at
        int visitas_count
        int guardados_count
        int busquedas_count
        numeric calificacion_promedio
    }
    pedidos {
        uuid id PK
        uuid user_id FK
        uuid vendedor_id FK
        string estado
        uuid orden_compra_id FK
        numeric total
    }
    stock {
        uuid product_id PK_FK
        numeric cantidad_disponible
        numeric cantidad_reservada
        timestamptz updated_at
    }
    movimientos_stock {
        uuid id PK
        uuid product_id FK
        string tipo
        numeric cantidad
        uuid pedido_id FK
        timestamptz created_at
    }
    facturas {
        uuid id PK
        uuid orden_compra_id FK_UK
        string numero_fiscal UK
        numeric total
        timestamptz created_at
        uuid created_by FK
    }
    ordenes_compra {
        uuid id PK
        string numero UK
        numeric total
        uuid created_by FK
    }
```

Relaciones clave en texto:

- `users 1 — 0..N favoritos N — 1 productos`
- `users 1 — 0..N calificaciones N — 1 productos` (con `UNIQUE(user,producto)`)
- `users 1 — 0..1 carritos 1 — N carrito_items N — 1 productos`
- `productos N — M categorias` vía `producto_categorias`
- `productos N — M etiquetas` vía `producto_etiquetas`
- `unidades_medida 1 — N productos`
- `users 1 — N pedidos` (como `user_id` cliente) y `users 0..1 — N pedidos` (como `vendedor_id`)
- `pedidos N — 1 ordenes_compra` (consolidación `RN-29`; `orden_compra_id` nullable)
- `ordenes_compra 1 — 0..1 facturas` (RN-36; `facturas.orden_compra_id UNIQUE`, `RESTRICT` impide borrar OC facturada)
- `pedidos N — 1 facturas` indirecto vía `orden_compra` (RN-36)
- `productos 1 — 1 stock` (RN-35; `stock.product_id PK FK`)
- `productos 1 — N movimientos_stock` y `pedidos 1 — N movimientos_stock` (RN-35; trazabilidad `tipo` reserva/confirmacion/devolucion)
- `pedidos 1 — N pedido_items N — 1 productos`
- `productos 1 — N visitas` (con `user_id` nullable + `visitor_cookie` nullable)

## Notas

### Soft delete vs hard delete

- **Usuarios**: nunca `DELETE` físico. `is_active=false` (`RN-17`). El `id` permanece estable para que la reactivación nativa (`ADR-002`) recupere pedidos, favoritos, calificaciones y visitas sin migración. `ON DELETE CASCADE` en tablas hijas existe solo como salvaguarda; en operación normal no se borra el usuario. Si el usuario opta por eliminar sus pedidos al darse de baja (`RF-18`/`RN-19`), se borran solo `pedidos` en `pendiente`; las `ordenes_compra` nunca se eliminan.
- **Productos**: `DELETE` físico prohibido si existen referencias históricas (`pedido_items`, `calificaciones` con `RESTRICT`). Eliminar con historial es `UPDATE productos SET deleted_at=now(), estado_publicacion='oculto'` (`RN-32`). Los queries públicos siempre filtran `WHERE deleted_at IS NULL AND estado_publicacion='publicado'`. El admin ve todo. `producto_categorias`/`producto_etiquetas` se conservan para que el histórico se resuelva.
- **Pedidos**: `DELETE` físico solo si `estado='pendiente'` y por el creador (`RN-28`). El resto de estados son inmutables salvo transiciones de la máquina extendida por staff (RN-28). `entregado` y `rechazado` son terminales.
- **Stock** (RN-35): `stock` y `movimientos_stock` nunca se borran físicamente salvo `ON DELETE CASCADE` por borrado de producto (que a su vez está bloqueado por `RESTRICT` si hay historial). La corrección de inventario futura usará nuevo tipo de movimiento, no `DELETE`.
- **Facturas** (RN-36): nunca `DELETE`; `RESTRICT` sobre `facturas.orden_compra_id` impide borrar la OC facturada. `numero_fiscal` inmutable.
- **Vendedor de baja** (`RN-27`/`ADR-007`): `ordenes_compra.created_by` queda congelado; `pedidos.vendedor_id` de pedidos `pendiente` es reasignable por admin con auditoría (tabla de auditoría futura o `updated_at` + log de aplicación).

### Counter caches

- `productos.visitas_count`, `guardados_count`, `busquedas_count`, `calificacion_promedio`, `calificacion_cantidad` son **caches desnormalizados** para ordenar y mostrar sin agregaciones en cada request (`RN-07`/`RN-30`).
- Actualización **transaccional** junto al evento fuente:
  - `favoritos INSERT/DELETE` → `guardados_count ±1` (`TC-RN09-01`)
  - `visitas INSERT` (tras pasar dedup) → `visitas_count+1`; si `origen='busqueda'` también `busquedas_count+1` (`TC-RN30-01`)
  - `calificaciones INSERT/UPDATE/DELETE` → recálculo `AVG`/`COUNT` en la misma transacción (`TC-RN33-02`)
- Alternativa futura: trigger `AFTER INSERT OR DELETE` en `favoritos`/`visitas`/`calificaciones` que mantenga el contador; para MVP se prefiere lógica explícita en servicio para testabilidad (`testing/00-strategy.md` exige PostgreSQL real en tests).
- Piso `0` garantizado por `CHECK (...) >=0` y `GREATEST(0, ...)` en `UPDATE`.

### Búsqueda, filtros y relevancia (`RN-04`, `RN-30`, `RN-07`)

- **Búsqueda combinable** (`RN-04`/`RN-05`): un único query combina `titulo ILIKE` (trgm), `datos_tecnicos` (`JSONB @>`, `@@` o `ILIKE` sobre cast a texto) y joins a `producto_categorias`/`producto_etiquetas`. Ejemplo canónico:
  ```sql
  SELECT p.* FROM productos p
  LEFT JOIN producto_categorias pc ON pc.product_id=p.id
  LEFT JOIN producto_etiquetas pt ON pt.product_id=p.id
  WHERE p.deleted_at IS NULL AND p.estado_publicacion='publicado'
    AND (p.titulo ILIKE '%'||:q||'%' OR p.datos_tecnicos::text ILIKE '%'||:q||'%')
    AND (:cat IS NULL OR pc.categoria_id=:cat)
    AND (:tag IS NULL OR pt.etiqueta_id IN (:tags))
  ORDER BY ...;
  ```
  Índices `GIN` en `titulo` (trgm) y `datos_tecnicos` (jsonb) evitan seq scan.
- **Relevancia** (`RN-30`): `ORDER BY busquedas_count DESC` — solo cuentan aperturas con `visitas.origen='busqueda'`, no apariciones en listados (evita inflación por paginación). Histórico acumulado en MVP; decaimiento temporal queda para iteración posterior.
- **Otros órdenes** (`RN-07`): `más reciente` → `created_at DESC`; `precio más alto/bajo` → `precio DESC/ASC`; `A-Z/Z-A` → `titulo ASC/DESC` con `COLLATE`; `con descuento` queda como criterio reservado (columna futura).
- **Autocompletado etiquetas** (`RN-03`): `SELECT nombre FROM etiquetas WHERE nombre ILIKE '%'||:frag||'%' ORDER BY nombre LIMIT 10` usando `idx_etiquetas_nombre_trgm`.

### Bootstrap `users` (`ADR-006`, `BOOT-01..04`)

- En el primer arranque, si `SELECT 1 FROM users WHERE role='administrador' LIMIT 1` no devuelve filas y `ADMIN_INITIAL_USER`/`ADMIN_INITIAL_PASSWORD` están seteadas, se crea el admin con `must_change_password=true`.
- Si ya existe un admin, no-op idempotente (`BOOT-01`).
- La contraseña se valida contra `RN-15` antes de hashear; si falla, el arranque aborta ruidoso (`BOOT-02`).
- `ADMIN_INITIAL_USER` es el `email` del admin (alias documentado de `ADMIN_INITIAL_EMAIL`).
- Tras el primer login forzado, la única contraseña válida es la nueva (`BOOT-04`).

### Seeds iniciales

- **Categorías** y **etiquetas** se siembran por migración Alembic (insert idempotente con `ON CONFLICT DO NOTHING`).
- **Unidades**: al menos `unidades`, `cm`, `m`, `kg`.
- **Productos**: 2–3 productos modelo (`RF-24`) con `unidad_venta_id` válida, al menos una categoría y `precio>0`; `imagen=NULL`. Cada producto sembrado crea su fila `stock` con `cantidad_disponible` inicial (ej. 100) y `cantidad_reservada=0`.
- **Stock**: migración idempotente crea `stock` para productos existentes sin fila (backfill `disponible=0` o valor de negocio).

### Testing y trazabilidad

- Cada `RN-xx` mapeada arriba debe tener al menos un happy path y un bad path (`testing/00-strategy.md TEST-01`, `testing/01-test-cases.md`).
- Tests de API/integración usan **PostgreSQL real** (no SQLite) para validar `CHECK`, `UNIQUE`, `GIN`, `FK RESTRICT` y ventanas de dedup (`TC-RN08-01/02`, `TC-RN32-01`, `TC-RN28-01`, `TC-RN29-01/02`, `TC-RN33-01/02`, `TC-BOOT-01/02`, `TC-RN34-01`, `TC-RN35-*`, `TC-RN36-*`, `TC-RN37-01`).

### Evolución sin rediseño

- Nuevas unidades: `INSERT INTO unidades_medida`.
- Nuevas categorías: `INSERT` controlado por admin (taxonomía cerrada, no por usuario final).
- Nuevas etiquetas: `INSERT` libre por vendedor/admin.
- Descuento futuro: añadir `productos.precio_descuento` o tabla `descuentos` sin tocar PKs existentes.
- Auditoría de reasignación (`RN-27`): añadir tabla `pedido_reasignaciones (id, pedido_id, from_vendedor_id, to_vendedor_id, by_admin_id, at)` cuando se requiera trazabilidad completa.
