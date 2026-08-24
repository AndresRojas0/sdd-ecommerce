# Visión general de UI

Interfaz de la tienda pública (storefront SvelteKit, mobile-first). El
panel admin tiene su propia UI en su proyecto independiente.

## Fuente de verdad visual

`docs/ui/DESIGN.md` define la identidad extraída ("Wickes Bold Retail"):
navy `#003087`, dorado `#ffd700`, naranja de acento `#e85d04`, tipografías
condensadas Oswald / Roboto Condensed, esquinas rectas (radius 0) con
sombras offset planas (3px 3px). Este documento NO reemplaza esos tokens:
los mapea a la implementación.

## Estrategia de tema

| Aspecto | Decisión |
| ------- | -------- |
| Framework visual | **shadcn-svelte** sobre Tailwind CSS. |
| Modo oscuro | Sí. Mecanismo: **dos juegos de tokens CSS** (claro + oscuro) aplicados por clase `.dark` en `<html>`. |
| Preferencia inicial | `prefers-color-scheme`; elección del usuario persistida en `localStorage`. Script inline temprano para evitar flash de tema incorrecto. |
| Paleta | Cálida referida a la temática ferretería/DIY dentro de la identidad Wickes: naranja y dorado como acción/acento; navy como base profunda. |

## Estructura global persistente

```
┌──────────────────────────────────────────────┐
│ Navbar (logo "Punto App" · búsqueda ·        │
│         carrito · login/avatar)              │
├──────────────────────────────────────────────┤
│ Hero + buscador con limpieza de filtros      │  ← solo Home
├──────────────────────────────────────────────┤
│ Contenido (cards, detalle, etc.)             │
├──────────────────────────────────────────────┤
│ Footer persistente en toda la app            │
└──────────────────────────────────────────────┘
```

## Reglas transversales

- **Skeletons en toda la aplicación**: toda carga de datos muestra skeleton
  con la forma del contenido final (card, detalle, líneas de pedido).
- **Estados vacíos y errores**: diseñados explícitamente (ver
  `01-pages.md`); errores de red usan `Alert` destructiva de shadcn.
- Mobile-first: se diseña ≤600px primero y se escala.
