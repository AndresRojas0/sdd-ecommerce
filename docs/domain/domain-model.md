# Modelo de dominio

Modelo conceptual del sistema (primera iteración). Debe entenderse sin
leer código.

## Conceptos

| Concepto | Descripción |
| -------- | ----------- |
| **Usuario** | Persona registrada. Definido por `email` (identidad única), `display_name`, `avatar`, `password` (hash), fecha de creación de perfil, fecha/hora de último login y `is_active` (baja lógica). Consulta, busca, filtra, guarda favoritos, genera pedidos y califica productos. |
| **Rol** | Perfil de autorización: `Visitante anónimo`, `Comprador`, `Vendedor`, `Administrador` (ver `requirements/authentication.md`). |
| **Producto** | Ítem del catálogo. Atributos: `título`, `slug` (SEO), `descripción`, `componentes incluidos`, `datos técnicos`, `precio`, `imagen` (0..1, nula en MVP), unidad de venta (RN-23). Pertenece a una o más categorías, puede tener etiquetas y expone contadores de visitas y de guardados. |
| **Categoría** | Familia cerrada de productos (taxonomía controlada). Tiene slug propio. Ej.: `herramientas`, `electricidad`. |
| **Etiqueta (tag)** | Término descriptivo de vocabulario abierto y dinámico. Tiene slug propio. Ej.: `inoxidable`, `hexagonal`, `tornillos`. |
| **Unidad de medida** | Unidad de venta del producto, de registro abierto: unidades, cm/m (cables), kg (cañería por kilo), etc. Extensible sin rediseño (RN-23). |
| **Especificación técnica** | Atributo técnico que describe al producto y es buscable. Equivale a los "datos técnicos". |
| **Componentes incluidos** | Lista de elementos que vienen con el producto. |
| **Favorito** | Relación entre un usuario y un producto marcado como preferido. Alimentar el contador de guardados del producto. |
| **Visita** | Apertura del detalle de un producto por un visitante (autenticado o anónimo). Se deduplica por visitante y ventana de tiempo (ADR-001). |
| **Carrito** | Borrador de orden de compra: líneas de producto con cantidades, previsualizable antes de confirmar. |
| **Línea de pedido** | Par producto + cantidad dentro de un carrito o pedido. |
| **Pedido** | Solicitud generada por un comprador a partir del carrito. Atributos: líneas, precio subtotal, precio total, fecha de creación, usuario creador. Tiene estado y autor (RN-26). |
| **Orden de compra** | Documento comercial generado cuando Admin o Vendedor confirma un pedido. Conserva la relación con el usuario que lo creó. |
| **Calificación** | Valoración de 1 a 5 estrellas que un usuario emite sobre un producto. El producto expone el promedio `Σ estrellas / cantidad` (RN-21). |
| **Descuento** | Condición de precio promocional de un producto. Aparece como criterio de orden; definición detallada pendiente. |

## Ciclo de vida del pedido

```
Carrito ──confirmar──> Pedido [pendiente de validación] ──aceptar (Admin/Vendedor)──> Orden de compra
                              │
                              └──rechazar (Admin/Vendedor, con motivo)──> [rechazado]
```

- Solo el pedido `pendiente` es editable/eliminable por su creador (RN-28)
  y reasignable entre vendedores activos (RN-27).
- Antes de validar, el staff puede sanear líneas: corregir nombre,
  normalizar unidad/denominación (UC-AD17/AD18).

## Relaciones

- Un `Usuario` tiene un `Rol` que define sus capacidades.
- Un `Usuario` arma cero o más `Carritos`; cada `Carrito` contiene una o más `Líneas de pedido` y al confirmarse genera un `Pedido`.
- Una `Línea de pedido` referencia un `Producto` con una cantidad expresada en la unidad de venta del producto (RN-23).
- Un `Usuario` marca cero o más `Favoritos`; cada `Favorito` referencia un `Producto` e incrementa/decrementa su contador de guardados.
- Cada apertura de detalle registra una `Visita` sobre el `Producto`, deduplicada por visitante (ADR-001).
- Un `Usuario` emite cero o más `Calificaciones`; cada `Calificación` referencia un `Producto`.
- Un `Producto` pertenece a **una o más** `Categorías` (RN-01, relación N:M).
- Un `Producto` tiene cero o más `Etiquetas` (RN-02), relación también N:M con slug propio en cada término.
- Un `Producto` tiene datos técnicos (especificaciones), precio obligatorio y hasta una imagen.

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
                 pertenece-a (1..N)                           │  tiene (0..N)
   Categoría (slug) <─────────────────────────── Producto ───┴──> Etiqueta (slug)
                                                  │
                                                  └── título, slug, descripción,
                                                      componentes incluidos, datos técnicos,
                                                      precio, imagen (0..1), unidad de venta,
                                                      contadores (visitas, guardados)

UnidadDeMedida (registro abierto: un., cm, m, kg, ...) ──define la venta de──> Producto
```

> Detalle de atributos por entidad: pendiente para `entities.md` cuando
> el modelo se estabilice.
