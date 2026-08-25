# Páginas y estados

Definición de pantallas de la tienda pública, navegación y estados.

## Rutas

| Ruta | Pantalla |
| ---- | -------- |
| `/` | Home: hero + buscador + grilla de productos |
| `./producto/<slug>` | Detalle de producto (RN-20) |
| `/carrito` | Carrito completo: edición de líneas y previsualización del pedido |
| `/mis-pedidos` | Pedidos del usuario autenticado |
| `/mis-favoritos` | Favoritos del usuario autenticado |
| `/login`, `/registro` | Autenticación (AUTH-05) |

> **Carrito con doble acceso** (decisión de negocio): drawer lateral rápido
> (`CartSheet`) desde el navbar para previsualizar sin salir de la página
> (RN-12), y página propia `/carrito` para editar líneas con comodidad y
> confirmar el pedido. El ícono del navbar abre el drawer; el drawer ofrece
> "Ver carrito completo" hacia `/carrito`.

## Home

```
Navbar ────────────────────────────────────────────────
[ logo "Punto App" ]        [ búsqueda ] [🛒] [ Ingresar ]
  ↳ logueado: + Mis Pedidos · Mis Favoritos · avatar/menú

Hero (fondo navy, headline Oswald blanco/dorado)
┌────────────────────────┬──────────────────────────┐
│ Frase del espíritu     │ Buscador                 │
│ + subcopy              │ [ input live ]           │
│                        │ chips de filtros activos │
│                        │ con ✕ para limpiar       │
└────────────────────────┴──────────────────────────┘

Grilla de ProductCards → scroll infinito
Footer persistente
```

### Copy del hero (propuesto)

> **"El punto de partida de tu próximo proyecto."**
> Herramientas, materiales y repuestos. Buscá por nombre o dato técnico,
> filtrá por categoría y etiqueta, y encontralo al toque.

Juega con la marca ("Punto") y declara el modelo real: búsqueda por nombre
y datos técnicos (RN-04) combinable con filtros de categoría y tags (RF-04).

### Navbar reactivo

| Estado | Elementos |
| ------ | --------- |
| Anónimo | Logo, buscador, carrito, botón **Ingresar** |
| Logueado | Ídem + enlaces **Mis Pedidos** y **Mis Favoritos**; el botón pasa a menú de usuario (avatar): Mi perfil · Mis pedidos · Mis favoritos · Cerrar sesión |

## Card de producto

Anatomía (de arriba hacia abajo):

1. **Imagen** superior, cuadrada 400×400, mockeada con paleta de marca:
   `https://placehold.co/400x400/003087/ffd700?text=Punto+App` (RN-13:
   campo imagen nulo en MVP; el mock se reemplaza por imagen real sin
   cambiar el layout).
2. **Badges de categorías** con el `color` hex de cada categoría (fondo del
   badge; texto blanco/navy según luminancia). Máximo visible: 2 + "+N".
3. **Título** (Oswald, 1–2 líneas).
4. **Calificación**: estrellas fraccionales (RN-21) + cantidad.
5. **Contador de favoritos** (guardados, RN-09).

Click en cualquier parte de la card → navega a `./producto/<slug>`.

Ídem para `/mis-pedidos`: mismas cards + línea de estado del pedido
(pendiente/aceptado/rechazado, RN-28).

## Detalle de producto (`./producto/<slug>`)

Imagen grande (mock), título, badges de categorías, calificación completa,
contador de visitas y de guardados, precio, descripción, componentes
incluidos, datos técnicos (tabla), selector de cantidad en unidad de venta
(RN-23), acciones: agregar al carrito, favorito, compartir (RF-22).

## Buscador — mecánica

- **Live search con debounce de 300ms**; dispara desde 2 caracteres.
- Combina texto + filtros de categoría/tag en una consulta (RN-04/RN-05).
- Los filtros aplicados se muestran como **chips removibles** junto al
  buscador; botón "Limpiar filtros".
- Resultados con **scroll infinito** (no paginación): sentinel con
  IntersectionObserver; al cambiar filtros/búsqueda se resetea la grilla.
- Skeletons durante carga; sin resultados → estado vacío temático.

## Estados vacíos y errores

| Caso | Tratamiento |
| ---- | ----------- |
| Búsqueda sin resultados | Ilustración temática (herramienta cruzada/tuerca solitaria) + "No encontramos nada para tu búsqueda" + CTA limpiar filtros |
| Favoritos/pedidos vacíos | Mensaje + CTA hacia el catálogo |
| 404 (ruta inexistente / slug inválido) | Página temática: fondo navy, headline Oswald "404 — Esta pieza no está en el taller", ilustración tuerca/herramienta, CTA volver al inicio. Mismo tratamiento si un slug no existe |
| Error de red / servidor | **Alert destructiva** de shadcn (rojo) persistente en la zona afectada, con acción Reintentar |
| Login fallido | Alert destructiva con mensaje específico (AUTH-05) |

## Footer persistente

En todas las rutas: logo, navegación mínima, toggle claro/oscuro, aviso de
versión MVP. Fondo navy con texto claro (ambos temas).
