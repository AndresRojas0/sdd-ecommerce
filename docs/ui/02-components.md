# Componentes de UI

Inventario de componentes reutilizables y su base en shadcn-svelte.

## Primitivos shadcn-svelte utilizados

| Primitivo | Uso |
| --------- | --- |
| `Button` | CTAs, navbar, acciones de card/detalle. Variantes: default (navy), secondary (gold), destructive |
| `Input` | Buscador, formularios de auth y perfil |
| `Card` | Card de producto, bloques del detalle |
| `Badge` | Badges de categoría (color dinámico por `category.color`) y de estado de pedido |
| `Sheet` | **Carrito**: drawer lateral previsualizable desde el navbar (RN-12) sin salir de la página |
| `DropdownMenu` | Menú de usuario logueado (perfil/pedidos/favoritos/salir) |
| `Skeleton` | Estados de carga en toda la app |
| `Alert` | Errores de red/servidor y login fallido (variante destructive) |
| `Separator`, `Table` | Datos técnicos del detalle |

## Compuestos del proyecto

### `<ProductCard>`
Imagen mock 400×400 · badges de categoría coloreados · título ·
estrellas fraccionales + cantidad · contador de favoritos. Click completo
→ `./producto/<slug>`. Estados: loading (skeleton), normal.
Reutilizada en Home y `/mis-pedidos` (con badge de estado).

### `<StarRating>` 
Render fraccional RN-21: promedio 4.15 → 4 estrellas llenas + 15% de
relleno en la quinta. Implementación: contenedor de 5 estrellas outline +
capa recortada (`clip-path`/width %) con estrellas llenas doradas.

### `<SearchBar>`
Input live con debounce 300ms (≥2 caracteres), chips removibles de filtros
activos, botón "Limpiar filtros". Emite consulta combinada (RN-04).

### `<CategoryBadge>`
Badge con fondo `category.color`; texto blanco o navy según luminancia
(contraste WCAG AA, regla de `DESIGN.md`). Máximo 2 + "+N" en cards.

### `<InfiniteGrid>`
Grilla de productos con IntersectionObserver; expone estados: loading,
cargando-más, vacío, error (Alert destructiva + Reintentar).

### `<CartSheet>`
Drawer lateral: líneas producto+cantidad+subtotal, total general,
CTA confirmar pedido (UC-B05). Accesible desde el ícono del navbar.

### `<ThemeToggle>`
Claro/oscuro; persiste en `localStorage('theme')`.

## Reglas

- Todo componente nuevo se documenta aquí en el mismo cambio que su
  creación (regla del README de la sección).
- Los colores de badge NUNCA se hardcodean en componentes: siempre leen el
  campo `color` de la categoría.
