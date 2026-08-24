# Alcance

## En alcance (primera iteración)

- Registro y autenticación de usuarios con roles (Administrador, Vendedor, Comprador).
- Consulta pública del catálogo de productos.
- Búsqueda combinable por nombre y especificaciones técnicas.
- Filtrado por categoría y etiquetas, combinable con la búsqueda.
- Autocompletado de etiquetas mientras se escribe.
- Ordenamiento de resultados: relevancia, más reciente, con descuento, precio más alto, precio más bajo, A-Z, Z-A.
- Contador de visitas por producto (con deduplicación de recargas) y contador de guardados.
- Gestión de favoritos (guardar productos).
- Carrito con productos y cantidades; previsualización antes de generar el pedido.
- Calificación de productos.
- Productos con precio obligatorio e imagen única opcional (nula en la primera etapa).

## Fuera de alcance / pendiente de definición

| Tema | Estado |
| ---- | ------ |
| Pagos y medios de pago | No mencionado. Pendiente. |
| Envíos y logística | No mencionado. Pendiente. |
| Recuperación de contraseña | Diferida: requiere envío de correos, no configurado en esta etapa (AUTH-06). |
| Definición de descuento | Existe como criterio de orden ("con descuento"); falta definir mecánica (% vs. precio final, vigencia). |
| Definición de relevancia | Criterio de orden sin algoritmo definido todavía. |
| Estrategia de reactivación del usuario dado de baja | En decisión: opciones presentadas, ADR pendiente (RN-17). |

## Decisiones resueltas

1. ~~¿La consulta del catálogo es pública o requiere usuario registrado?~~ → **Pública**: solo favoritos, carrito, pedidos y calificaciones requieren sesión (RN-10).
2. ~~¿Existe un rol administrador que gestione el catálogo?~~ → **Sí**, con alcance total; rol Vendedor con capacidades definidas (ver pedidos, cargar pedidos por cliente, alta de productos y etiquetas).
3. ~~¿El pedido se genera directo o mediante un carrito previo?~~ → **Con carrito**: previsualizable antes de generar el pedido (RN-12).
4. ~~¿Quién confirma un pedido?~~ → **Admin o Vendedor** confirman y generan la orden de compra (RN-18).
5. ~~Recuperación de pedidos del usuario que vuelve~~ → **Reactivación nativa** (ADR-002).
6. ~~Autenticación~~ → **JWT con cookies** en frontend; panel admin como SPA Svelte independiente con login propio (ADR-003/005).
7. ~~Stack tecnológico~~ → **SvelteKit + FastAPI + PostgreSQL + REST**, Podman con imágenes públicas AWS (ADR-004); bootstrap de admin por env (ADR-006).

## Decisiones abiertas

1. ¿La ventana de deduplicación de visitas es fija (24 h) o configurable? (ADR-001)
2. Algoritmo de relevancia y mecánica de descuentos (ver `architecture/04-decisions.md`).
3. ¿Ocultar/despublicar productos sin eliminarlos? (UC-AD10, propuesto por negocio)
4. ¿Borrado lógico de productos con historial al eliminarlos? (UC-AD09)
5. Interpretación de "asociar pedido a un pedido existente" (UC-AD19).

## Límites explícitos del MVP

- Sin moderación de contenido (RN-25).
- Sin seguimiento social (RN-22): solo compartir producto.
- Imagen de producto nula en esta primera etapa (RN-13).
- Sin envío de correos electrónicos (AUTH-06).
