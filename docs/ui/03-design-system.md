# Sistema de diseño (mapeo a shadcn-svelte)

Implementación de los tokens de `DESIGN.md` como variables CSS de
shadcn-svelte, con soporte claro/oscuro.

## Mapeo de colores → variables shadcn

| Variable shadcn | Claro | Oscuro (propuesto) | Uso |
| --------------- | ----- | ------------------ | --- |
| `--primary` | navy `#003087` | navy claro `#3b62c4` | Botones primarios, navbar, hero |
| `--primary-foreground` | white `#ffffff` | white | Texto sobre primario |
| `--accent` / `--secondary` | gold `#ffd700` | gold `#e6c200` | CTAs secundarios, badges destacados |
| `--accent-foreground` | dark-navy `#1a1f3a` | dark-navy | Texto sobre dorado |
| `--destructive` | rojo estándar shadcn | ídem | Errores, alertas destructivas |
| `--background` | white `#ffffff` | `#12151f` (navy-negro) | Fondo de página |
| `--card` | light-gray `#f0f0f0` | `#1c2130` | Superficies de card |
| `--muted-foreground` | mid-gray `#666666` | `#9aa2b5` | Texto secundario |
| `--border` / `--input` | border-gray `#cccccc` | `#2a3040` | Bordes e inputs |
| Naranja acento | `#e85d04` | ídem (ya cálido) | Banner promocional, badge de oferta, sombra activa |

> El modo oscuro propuesto mantiene la identidad: navy más luminoso para
> acción, superficies navy-negro, dorado ligeramente atenuado para no
> vibrar sobre fondo oscuro. Valores finales ajustables en implementación.

## Tipografía

| Rol | Fuente | Peso/Tamaño clave |
| --- | ------ | ------------------ |
| Headings, nav, botones, badges | **Oswald** | 700; hero 56px→38px mobile (+17%) |
| Cuerpo y descripciones | **Roboto Condensed** | 400; 16px base (+14%) |

> **Escala incrementada** 2026-08-31: todos los tamaños +14–18% para mejorar legibilidad. Hero 48→56, sección 22.4→26, nav 12→14, categoría 14.4→17, body 14→16, small 12→14, badge 13.6→16, botón 19.2→22.

- Entrega: paquetes **@fontsource** self-hosted (sin CDN externo en
  runtime, coherente con contenedores Podman sin dependencias externas).
- Escala completa por rol: ver tabla "Type Scale Evidence" en `DESIGN.md`.

## Forma y elevación

- **Radius global**: `--radius: 0px`. Esquinas rectas en todo (botones,
  cards, inputs, badges). Prohibido mezclar esquinas redondeadas.
- **Sombras offset planas** estilo sello retro: `3px 3px 0px` (navy u
  orange según contexto), tokens de `DESIGN.md` ("Shadow Evidence").

## Espaciado

Grid base de 8px con la escala de `DESIGN.md` (`1.6 · 3 · 4 · 8 · 12 · 16
· 20 · 24 · 32`). En Tailwind esto equivale a usar la escala estándar
(1u = 8px); prohibido valores fuera de escala salvo casos justificados.

## Breakpoints

| Tier | Ancho | Estrategia |
| ---- | ----- | ---------- |
| Mobile (base) | ≤600px | Vertical stacking, densidad reducida |
| Tablet (propuesto) | 601–1024px | Grillas de 2–3 columnas |
| Desktop | >1024px | Grillas de 4+ columnas, hero expandido |

## Modo oscuro — mecánica

1. Tokens definidos como variables CSS en `:root` (claro) y `.dark`
   (oscuro).
2. Script inline en `<head>`: lee `localStorage('theme')`; si no existe,
   usa `prefers-color-scheme`; aplica clase `.dark` antes del primer paint.
3. Toggle manual en el footer/navbar persiste la elección.

## Skeletons

Regla: **toda** petición de datos renderiza skeleton con la geometría del
contenido final (cards con imagen+título+badges; detalle con bloques;
filas de pedidos). Nunca spinners genéricos como estado principal.
