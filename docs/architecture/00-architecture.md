# Arquitectura general

Componentes del sistema y su comunicación (primera iteración, post-stack
ADR-004/005).

## Componentes

| Componente | Tecnología | Responsabilidad |
| ---------- | ---------- | ---------------- |
| **Tienda pública (storefront)** | Svelte / SvelteKit (mobile-first) | Catálogo público, búsqueda/filtros/orden, slugs SEO, carrito, favoritos, calificaciones, login comprador. |
| **Panel de administración** | Svelte (SPA independiente) | ABM de catálogo, usuarios y roles; confirmación de pedidos → orden de compra. Consuma la API, nunca la DB directa (ADR-005). |
| **Backend** | FastAPI (REST) | Toda la lógica de negocio: dominio, reglas RN-01..RN-37 (incluye máquina extendida RN-28, stock RN-35, factura RN-36, totales del día RN-37), dos sistemas de autenticación aislados (tienda y admin), bootstrap de admin (ADR-006). |
| **Base de datos** | PostgreSQL | Persistencia relacional del modelo de dominio (N:M producto-categoría, producto-etiqueta, pedidos, stock 1:1, movimientos_stock, facturas 1:1 con OC, tokens de refresh hasheados). |

## Comunicación

```
[ Tienda SvelteKit ] ──REST + JWT cookies (audiencia tienda)──┐
                                                              ├──> [ FastAPI REST ] ──> [ PostgreSQL ]
[ Admin Svelte SPA  ] ──REST + JWT cookies (audiencia admin)──┘
```

- Un único backend expone superficies de endpoints separadas por audiencia.
- Los tokens llevan `aud`/`scope` distintos: el token de la tienda no
  autoriza endpoints de admin ni viceversa.
- El storefront usa SSR/SSG de SvelteKit para SEO (slugs RN-20).

## Notas preparadas para el futuro (fuera del MVP)

- **Imágenes**: el modelo ya reserva campo nullable en producto (RN-13); la
  carga y el storage se implementarán después, sin rediseño del contrato.
- **Emails**: recuperación de contraseña diferida (AUTH-06).
