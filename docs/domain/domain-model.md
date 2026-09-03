# Modelo de dominio

Modelo conceptual del sistema (primera iteración). Debe entenderse sin
leer código.

## Conceptos

| Concepto | Descripción |
| -------- | ----------- |
| **Usuario** | Persona registrada. Definido por `email` (identidad única), `display_name`, `avatar`, `password` (hash), fecha de creación de perfil, fecha/hora de último login y `is_active` (baja lógica). Consulta, busca, filtra, guarda favoritos, genera pedidos y califica productos. |
| **Rol** | Perfil de autorización: `Visitante anónimo`, `Comprador`, `Vendedor`, `Administrador` (ver `requirements/authentication.md`). |
| **Producto** | Ítem del catálogo. Atributos: `título`, `slug` (SEO), `descripción`, `componentes incluidos`, `datos técnicos`, `precio`, `imagen` (0..1, nula en MVP), unidad de venta (RN-23). Estado de publicación: publicado/oculto (RN-31); borrado lógico con historial (RN-32). Expone contadores de visitas (con origen, RN-08), búsquedas (RN-30) y guardados (RN-09). |
| **Categoría** | Familia cerrada de productos organizada como **árbol de 2 niveles** (taxonomía controlada, `RN-01`, `RN-38`). `parent_id UUID NULL FK → categorias.id` (`ON DELETE RESTRICT`): `NULL` = nivel 1 (categoría raíz), no NULL = nivel 2 (subcategoría hoja). MVP limita profundidad a **máx. 2**; `CHECK (parent_id IS NULL AND nivel=1 OR parent_id IS NOT NULL AND nivel=2)` y `parent_id` solo puede apuntar a nivel 1 (validado por `CHECK`/trigger + aplicación). Tiene `slug` único, `nombre` único y **`color`** (hex) para el badge en card/detalle. Ej.: `herramientas` (nivel 1) → `herramientas manuales` (nivel 2), `electricidad` → `iluminación`. Un **producto debe pertenecer a al menos una categoría hoja** (nivel 2); pertenecer solo a un padre no es válido. |
| **Colección** | Grupo **curado por Admin**, **transversal a categorías**, para descubrimiento/marketing (no es taxonomía ni filtro). Atributos: `nombre` (único), `slug` (único, `/colecciones/{slug}`), `descripcion` (nullable), `imagen` (nullable), `destacada` (boolean, para home). Relación **N:M** con `Producto` vía `coleccion_productos` (`orden` opcional). Un producto puede estar en 0..N colecciones; una colección en 0..N productos. Ej.: `Ofertas de invierno`, `Novedades`, `Kit obra`. |
| **Etiqueta (tag)** | Término descriptivo de vocabulario abierto y dinámico. Tiene slug propio. Ej.: `inoxidable`, `hexagonal`, `tornillos`. |
| **Unidad de medida** | Unidad de venta del producto, de registro abierto: unidades, cm/m (cables), kg (cañería por kilo), etc. Extensible sin rediseño (RN-23). |
| **Especificación técnica** | Atributo técnico que describe al producto y es buscable. Equivale a los "datos técnicos". |
| **Componentes incluidos** | Lista de elementos que vienen con el producto. |
| **Favorito** | Relación entre un usuario y un producto marcado como preferido. Alimentar el contador de guardados del producto. |
| **Visita** | Apertura del detalle de un producto por un visitante (autenticado o anónimo). Se deduplica por visitante y ventana de tiempo configurable (ADR-001) y registra su origen (directa o desde búsqueda, RN-30). |
| **Carrito** | Borrador de orden de compra: líneas de producto con cantidades, previsualizable antes de confirmar. Persistencia server-side por usuario autenticado; sobrevive logout y cambio de dispositivo (RN-34). |
| **Línea de pedido** | Par producto + cantidad dentro de un carrito o pedido. |
| **Pedido** | Solicitud generada por un comprador a partir del carrito. Atributos: líneas, precio subtotal, precio total, fecha de creación, usuario creador. Tiene estado y autor (RN-26). |
| **Orden de compra** | Documento comercial generado cuando Admin o Vendedor confirma un pedido. Conserva la relación con el usuario que lo creó. Puede consolidar N pedidos del mismo comprador (RN-29) y es origen de la Factura (RN-36). |
| **Stock** | Disponibilidad física por producto. Atributos: `cantidad_disponible` (unidades libres para vender) y `cantidad_reservada` (unidades comprometidas por pedidos aceptados aún no facturados). Relación 1:1 con Producto. Sus movimientos se registran en `movimientos_stock` con tipos `reserva` / `confirmacion` / `devolucion` (RN-35). |
| **Factura** | Documento fiscal emitido desde una orden de compra aceptada. Atributos: `numero_fiscal` único, `total`, `fecha` y emisor. Relación 1:1 con Orden de compra; N pedidos → 1 OC → 1 Factura (RN-36). Habilita el cálculo de totales del día (RN-37). |
| **Calificación** | Valoración de 1 a 5 estrellas que un usuario emite sobre un producto. El producto expone el promedio `Σ estrellas / cantidad` (RN-21). |
| **Descuento** | Condición de precio promocional de un producto. Aparece como criterio de orden; definición detallada pendiente. |

## Ciclo de vida del pedido

```
Carrito ──confirmar──> Pedido [pendiente] ──aceptar (Vendedor/Admin)──> [aceptado / En preparación] ──facturar (Admin)──> [facturado]
                              │                        │  ▲ reserva stock (RN-35)              │  ▲ confirma deducción (RN-35)
                              │                        │  │                                     │  │ genera Factura (RN-36)
                              │                        │  │                                     ▼  │
                              │                        │  └─────────────> [facturado] ──a logística (Admin/Logística)──> [en_logistica] ──entregar──> [entregado]
                              │                        │
                              └──rechazar (Vendedor/Admin, con motivo)──> [rechazado] (terminal, libera reserva RN-35)
                                     ▲                                                       (RN-29: N pedidos consolidables en 1 OC)
```

Estados extendidos (RN-28): `pendiente → aceptado (En preparación) → facturado → en_logistica → entregado`, más `rechazado` terminal. Transiciones permitidas y actor:

| Transición | Actor | Efecto stock (RN-35) |
|------------|-------|----------------------|
| `pendiente → aceptado` | Vendedor o Administrador | **Reserva**: `disponible −= cantidad`, `reservada += cantidad`; registra `movimientos_stock` tipo `reserva` |
| `pendiente → rechazado` | Vendedor o Administrador (con motivo) | Sin efecto stock (no hubo reserva) |
| `aceptado → facturado` | Administrador | **Confirmación**: `reservada −= cantidad` (la deducción ya se reflejó al reservar); registra `confirmacion`; genera `facturas` vinculada a la OC (RN-36) |
| `aceptado → rechazado` | Vendedor o Administrador | **Devolución**: `disponible += cantidad`, `reservada −= cantidad`; registra `devolucion` |
| `facturado → en_logistica` | Administrador / Logística | Sin efecto stock |
| `en_logistica → entregado` | Administrador / Logística | Sin efecto stock (terminal de éxito) |

- Solo el pedido `pendiente` es editable/eliminable por su creador (RN-28)
  y reasignable entre vendedores activos (RN-27). Un pedido `rechazado` es
  terminal: solo admite duplicarse como nuevo pendiente (RN-28).
- `aceptado`, `facturado`, `en_logistica` y `entregado` son estados progresivos no reversibles (salvo `aceptado → rechazado` con devolución de stock).
- Antes de validar, el staff puede sanear líneas: corregir nombre,
  normalizar unidad/denominación (UC-AD17/AD18).
- Varios pedidos pendientes del mismo comprador pueden consolidarse en una
  única orden de compra (RN-29, UC-AD19): la relación Pedido→Orden de
  compra es **N:1**. La facturación opera sobre la OC (RN-36), por lo que todos los pedidos consolidados avanzan juntos a `facturado`.

## Relaciones

- Un `Usuario` tiene un `Rol` que define sus capacidades.
- Un `Usuario` arma cero o más `Carritos`; cada `Carrito` contiene una o más `Líneas de pedido` y al confirmarse genera un `Pedido`.
- Una `Línea de pedido` referencia un `Producto` con una cantidad expresada en la unidad de venta del producto (RN-23).
- Un `Usuario` marca cero o más `Favoritos`; cada `Favorito` referencia un `Producto` e incrementa/decrementa su contador de guardados.
- Cada apertura de detalle registra una `Visita` sobre el `Producto`, deduplicada por visitante (ADR-001).
- Un `Usuario` emite cero o más `Calificaciones`; cada `Calificación` referencia un `Producto`.
- Un `Producto` pertenece a **una o más** `Categorías` **hoja** (nivel 2, `RN-01`/`RN-38`, relación N:M vía `producto_categorias`); validación de aplicación exige `COUNT(hoja) >= 1`. No basta con asignar solo una categoría padre.
- Un `Producto` puede pertenecer a **cero o más** `Colecciones` (`RN-39`, N:M vía `coleccion_productos`); la colección es curada por Admin y transversal a categorías — no es filtro taxonómico sino navegación directa (`/colecciones/{slug}`) y bloque de descubrimiento (`destacada` en home).
- Un `Producto` tiene cero o más `Etiquetas` (RN-02), relación también N:M con slug propio en cada término.
- Un `Producto` tiene datos técnicos (especificaciones), precio obligatorio y hasta una imagen.
- Un `Producto` tiene **un** `Stock` (relación 1:1, RN-35); `Stock` afectado por las transiciones de `Pedido` (`reserva`/`confirmacion`/`devolucion`) y trazado en `movimientos_stock`.
- Un `Pedido` se vincula a una `Orden de compra` (N:1, RN-29); una `Orden de compra` genera **una** `Factura` (1:1, RN-36). Indirectamente, `Pedido N — 1 Factura` vía `orden_compra`.

## Diagrama conceptual

```
                 Rol
                  │
Usuario ──arma──> Carrito ──líneas──> LíneaDePedido ──> Producto
   │                                     (producto+cantidad) │
   ├──marca──> Favorito ─────────────────────────────────────>│
   │                                                          │
   ├──emite──> Calificación (1..5 ★) ────────────────────────>│
   │                                                          │
   └──visitante──> Visita (dedup ADR-001) ───────────────────>│
                                                              │
                  pertenece-a (1..N hoja)                      │  tiene (0..N)
    Categoría (árbol 2 niveles, slug) <───────── Producto ───┴──> Etiqueta (slug)
                  ▲ parent_id → Categoría (nivel 1)            │
                  │ nivel 2 = hoja                              ├──en──> Colección (slug, destacada)  N:M transversal
                                                  │
                                                  └── título, slug, descripción,
                                                      componentes incluidos, datos técnicos,
                                                      precio, imagen (0..1), unidad de venta,
                                                      contadores (visitas, guardados)

UnidadDeMedida (registro abierto: un., cm, m, kg, ...) ──define la venta de──> Producto
```

## Stock y Factura — notas de comportamiento

- **Stock (RN-35)**: cada producto mantiene una fila en `stock` con `cantidad_disponible` y `cantidad_reservada`. La disponibilidad real para nuevos pedidos es `disponible`; la reservada no está vendida en firme hasta `facturado`. Todo cambio genera un `movimientos_stock` (`reserva` al aceptar, `confirmacion` al facturar, `devolucion` al rechazar un aceptado). No hay columna `stock` directa en `productos`.
- **Factura (RN-36)**: se emite una única vez desde una `orden_compra` aceptada; `numero_fiscal` es único e inmutable y `total` replica el total de la OC al momento de facturar. Una OC no facturable es aquella sin pedidos en estado `aceptado` o ya facturada.
- **Totales del día (RN-37)**: widget de dashboard (no columna kanban) que suma `facturas.total` del día corriente. Ver `use-cases/administrador.md` (UC-AD28) y `requirements/business-rules.md`.

> Detalle de atributos por entidad: pendiente para `entities.md` cuando
> el modelo se estabilice.
