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
- Flujo de pedidos extendido: `pendiente → aceptado (En preparación) → facturado → en_logistica → entregado` + `rechazado` terminal, con kanban de 5 columnas (Recibido / En preparación / Facturación / Logística / Entregado) (RN-28).
- Stock por producto (`stock` 1:1 + `movimientos_stock` reserva/confirmacion/devolucion) acoplado a transiciones de pedido (RN-35).
- Factura fiscal por orden de compra (`facturas` 1:1 con OC, `numero_fiscal` único) (RN-36).
- Totales del día: widget de dashboard `SUM(facturas.total)` del día corriente, no columna kanban (RN-37).
- Calificación de productos.
- Productos con precio obligatorio e imagen única opcional (nula en la primera etapa).

## Fuera de alcance / pendiente de definición

| Tema | Estado |
| ---- | ------ |
| Pagos y medios de pago | No mencionado. Pendiente. |
| Envíos y logística | No mencionado. Pendiente. |
| Recuperación de contraseña | Diferida: requiere envío de correos, no configurado en esta etapa (AUTH-06). |
| Definición de descuento | Existe como criterio de orden ("con descuento"); falta definir mecánica (% vs. precio final, vigencia). |

## Decisiones resueltas

1. ~~¿La consulta del catálogo es pública o requiere usuario registrado?~~ → **Pública**: solo favoritos, carrito, pedidos y calificaciones requieren sesión (RN-10).
2. ~~¿Existe un rol administrador que gestione el catálogo?~~ → **Sí**, con alcance total; rol Vendedor con capacidades definidas (ver pedidos, cargar pedidos por cliente, alta de productos y etiquetas).
3. ~~¿El pedido se genera directo o mediante un carrito previo?~~ → **Con carrito**: previsualizable antes de generar el pedido (RN-12).
4. ~~¿Quién confirma un pedido?~~ → **Admin o Vendedor** confirman y generan la orden de compra (RN-18).
5. ~~Recuperación de pedidos del usuario que vuelve~~ → **Reactivación nativa** (ADR-002).
6. ~~Autenticación~~ → **JWT con cookies** en frontend; panel admin como SPA Svelte independiente con login propio (ADR-003/005).
7. ~~Stack tecnológico~~ → **SvelteKit + FastAPI + PostgreSQL + REST**, Podman con imágenes públicas AWS (ADR-004); bootstrap de admin por env (ADR-006).

## Decisiones abiertas

1. Algoritmo de descuentos y su mecánica (% vs. precio final, vigencia) — único criterio de orden pendiente de definición fina.
2. Ajustes manuales de stock / inventario (tipo `ajuste` en `movimientos_stock`) — fuera del MVP inicial.

## Flujo extendido confirmado por negocio

Máquina de pedidos + stock + factura (RN-28/RN-35/RN-36/RN-37) está **en alcance** y confirmada. Implica: kanban de 5 columnas + widget totales del día, `stock`/`movimientos_stock` y `facturas` en el modelo físico (`domain/data-model.md` §16-17), y UC-AD25..AD28 / UC-V10..V11 en los casos de uso.

## Decisiones resueltas (adicionales)

1. ~~Consolidación de pedidos~~ → **solo pedidos del mismo comprador** (RN-29).
2. ~~Ventana de deduplicación de visitas~~ → **configurable** por entorno, default propuesto 24 h (RN-08, ADR-001).
3. ~~Algoritmo de relevancia~~ → **por más buscados**: aperturas de detalle con origen en búsqueda suman puntos al producto (RN-30).
4. ~~Ocultar/despublicar productos~~ → **incorporado**: reversible, permanece en DB (RN-31, UC-AD10).
5. ~~Eliminación de productos con historial~~ → **borrado lógico**, referencias históricas intactas (RN-32, UC-AD09).
6. ~~¿Quién puede calificar?~~ → **solo con pedido aceptado** que incluya el producto (RN-33).
7. ~~Destino de pedidos rechazados~~ → terminal; **duplicable como nuevo pedido pendiente** con motivo visible (RN-28).
8. ~~Persistencia del carrito~~ → **server-side por usuario autenticado**; anónimo dispara prompt de login (RN-34).

## Límites explícitos del MVP

- Sin moderación de contenido (RN-25).
- Sin seguimiento social (RN-22): solo compartir producto.
- Imagen de producto nula en esta primera etapa (RN-13).
- Sin envío de correos electrónicos (AUTH-06).
