# Requisitos funcionales

Funcionalidades que debe ofrecer la aplicación (primera iteración).

| ID | Requisito | Descripción |
| -- | --------- | ----------- |
| RF-01 | Registro y autenticación | El usuario puede registrarse en la aplicación y autenticarse. |
| RF-02 | Consulta de catálogo | El usuario puede consultar los productos del catálogo. |
| RF-03 | Búsqueda de productos | El usuario puede buscar productos por nombre o por especificaciones técnicas (datos técnicos). |
| RF-04 | Filtrado de productos | El usuario puede filtrar productos por categoría y por etiquetas. Los filtros son **combinables entre sí y con la búsqueda** (RF-03): categorías, tags, nombre y especificaciones técnicas pueden aplicarse juntos. |
| RF-05 | Autocompletado de etiquetas | Mientras el usuario escribe una etiqueta, el sistema sugiere etiquetas existentes que contienen el texto ingresado. Ej.: `tor` → `tornillos`, etc. |
| RF-06 | Favoritos | El usuario puede guardar productos como favoritos y consultarlos. |
| RF-07 | Pedidos | El usuario puede generar pedidos de productos. |
| RF-08 | Calificaciones | El usuario puede calificar productos. |
| RF-09 | Ordenamiento de resultados | Los resultados de búsqueda/filtrado pueden ordenarse por: relevancia, más reciente, con descuento, precio más alto, precio más bajo, A-Z, Z-A. |
| RF-10 | Administración del catálogo | El administrador tiene alcance total: ABM de productos, categorías, etiquetas y usuarios (ver `authentication.md`). |
| RF-11 | Rol vendedor | Ver pedidos generados y su estado; cargar pedidos en nombre de un cliente; agregar productos y sus etiquetas. |
| RF-12 | Contador de visitas | El sistema registra cuántas visitas recibe un producto. Una visita es la apertura del detalle del producto. La recarga de página no incrementa el contador más de una vez (ver RN-08 y ADR-001). |
| RF-13 | Contador de guardados | El sistema registra cuántas veces se guardó un producto en favoritos; se decrementa si se anula el guardado. |
| RF-14 | Carrito y pedido | Los productos tienen precio y son seleccionables con cantidades para armar una orden de compra, previsualizable en un carrito antes de generar el pedido. |
| RF-15 | Imagen de producto | Cada producto admite hasta una imagen representativa. En esta primera etapa el campo queda nulo (MVP). |
| RF-16 | Registro y login | El usuario se registra con email único, display-name y contraseña (política AUTH-04). Login con email + contraseña con mensaje de éxito o error específico (AUTH-05). Se registra fecha/hora del último login. |
| RF-17 | Recuperación de contraseña | El usuario puede recuperar su contraseña si la olvida. **Diferida**: requiere envío de correos electrónicos, no configurado en esta etapa (AUTH-06). |
| RF-18 | Darse de baja | El usuario puede darse de baja. La baja es lógica (`is_active = false`): conserva visitas, favoritos y pedidos. Al eliminarse, el usuario puede optar por eliminar también los pedidos que cargó (sujeto a RN-19). |
| RF-19 | Confirmación de pedido | El Admin o el Vendedor confirma un pedido de productos y genera la orden de compra correspondiente (RN-18). |
| RF-20 | Slugs SEO | Productos, categorías y etiquetas se exponen mediante URLs con slug único (RN-20). |
| RF-21 | Promedio de calificaciones | Los productos muestran el promedio de estrellas (`Σ estrellas / cant. calificaciones`) con render fraccional: 4.15 → 4 estrellas llenas + fracción de la quinta (RN-21). |
| RF-22 | Compartir producto | El usuario puede compartir un producto (enlace público con slug). Sin seguimiento entre usuarios en el MVP (RN-22). |
| RF-23 | Unidades de venta | Cada producto define su unidad de venta del registro abierto (unidades, cm/m, kg, ...) y las cantidades se expresan en esa unidad (RN-23). |
| RF-24 | Catálogo sembrado | El catálogo arranca con 2–3 productos modelo; el staff crea el resto (Vendedor: alta; Admin: CRUD completo) (RN-24). |
| RF-25 | Panel admin separado | Aplicación Svelte independiente que consume la API REST del backend, con login propio y aislado (AUTH-10, ADR-005). |
| RF-26 | Bootstrap de admin | El backend crea el administrador inicial desde variables `ADMIN_INITIAL_*` en el primer arranque y fuerza el cambio de contraseña en el primer login (AUTH-11, ADR-006). |
| RF-27 | Stack definido | SvelteKit (tienda), Svelte SPA (admin), FastAPI REST, PostgreSQL, Podman con imágenes públicas de AWS ECR Public (ADR-004). |
| RF-28 | Perfil y avatar | El usuario autenticado edita su perfil (display-name) y cambia su avatar. |
| RF-29 | Cambio de contraseña logueado | Con contraseña actual válida + nueva según política; invalida refresh tokens activos. |
| RF-30 | Edición y baja de pedido | El comprador edita o elimina sus pedidos solo mientras no fueron confirmados como orden de compra (RN-18/RN-19). |
| RF-31 | Reactivación de cuenta | Login con credenciales válidas sobre cuenta dada de baja ofrece reactivación: mismo userId e historial íntegro (UC-C10, ADR-002). |
| RF-32 | Vendedor gestiona perfiles | Busca perfiles y consulta pedidos por usuario; puede editar datos de perfil (no rol ni contraseña). |

> Trazabilidad: cada requisito debería rastrearse hasta su implementación y
> sus casos de prueba (ver `testing/`).
