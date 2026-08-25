# Reglas de negocio

Reglas que gobiernan el comportamiento del sistema (primera iteración).
Son la fuente de verdad para los casos de prueba.

| ID | Regla |
| -- | ----- |
| RN-01 | **Categorías cerradas**: el conjunto de categorías es una taxonomía fija controlada por el sistema. Un producto pertenece a **una o más categorías** (evolución: originalmente era exactamente una). No se pueden crear categorías libres desde la interacción de usuario. |
| RN-02 | **Etiquetas abiertas**: el vocabulario de etiquetas es dinámico. Un producto puede tener cero o más etiquetas. Lista semilla inicial: `accesorio`, `acero`, `aluminio`, `bronce`, `cable`, `cobre`, `disco`, `hexagonal`, `inoxidable`, `llave`, `madera`, `metal`, `plástico`, `repuesto`, `tornillos`, `tuerca`, etc. |
| RN-03 | **Autocompletado de etiquetas**: al escribir una etiqueta, el sistema sugiere etiquetas existentes cuyo nombre contiene el texto ingresado. Ej.: `tor` → sugerencias que contienen "tor" (`tornillos`, etc.). Las etiquetas no son cerradas: la sugerencia predice sobre vocabulario existente. |
| RN-04 | **Búsqueda combinable**: la búsqueda opera sobre nombre del producto o especificaciones técnicas, y puede aplicarse **junto con** los filtros de categoría y etiquetas. Categorías, tags, nombre y datos técnicos se combinan para acotar resultados en una sola consulta. |
| RN-05 | **Filtrado combinable**: los filtros por categoría y por etiquetas pueden combinarse entre sí y con la búsqueda textual (RN-04). |
| RN-06 | **Usuario registrado requerido**: guardar favoritos, generar pedidos y calificar productos requieren un usuario registrado y autenticado. |
| RN-07 | **Ordenamientos soportados**: relevancia, más reciente, con descuento, precio más alto, precio más bajo, A-Z, Z-A. La **relevancia** ordena por los productos más buscados: cada apertura de detalle originada desde un resultado de búsqueda suma un punto de búsqueda al producto (RN-30). |
| RN-08 | **Visita = apertura de detalle**: contar una visita cuando un visitante despliega el detalle de un producto. El mismo visitante no incrementa el contador más de una vez por recarga (F5) dentro de una **ventana de deduplicación configurable** (valor por defecto propuesto: 24 h, parámetro de entorno). El método de identificación del visitante anónimo está definido en `decisions/ADR-001-conteo-visitas-anonimas.md`. La visita registra su **origen** (directa o desde resultados de búsqueda) para alimentar la relevancia (RN-30). |
| RN-09 | **Contador de guardados**: guardar un producto en favoritos incrementa su contador; anular el guardado lo decrementa (piso cero). |
| RN-10 | **Catálogo público**: consultar, buscar, filtrar y ordenar productos no requiere autenticación (ver `authentication.md`). |
| RN-11 | **Precio obligatorio**: todo producto publicable tiene un precio. Los productos son seleccionables con cantidades para armar un pedido mediante el carrito. |
| RN-12 | **Carrito previsualizable**: el pedido se arma como carrito (producto + cantidad) y debe poder previsualizarse antes de generarse. |
| RN-13 | **Imagen única opcional**: un producto admite hasta una imagen representativa; en la primera etapa el campo es nulo. |
| RN-14 | **Identidad por email**: el email es único por cuenta y es la clave de login. El usuario se completa con display-name, avatar, fecha de creación de perfil y fecha/hora de último login. |
| RN-15 | **Política de contraseña**: mínimo 8 caracteres, al menos una mayúscula, un número y un caracter especial. Se almacena solo como hash. |
| RN-16 | **Recuperación de contraseña diferida**: prevista en el diseño, no implementable hasta contar con envío de correos electrónicos. |
| RN-17 | **Baja lógica del usuario**: darse de baja setea `is_active = false` y NO borra nada: se conservan visitas, favoritos (con sus contadores) y pedidos. Si el usuario vuelve a la plataforma, recupera su historial automáticamente mediante la reactivación nativa (ADR-002). |
| RN-18 | **Confirmación de pedido**: un pedido pasa a **orden de compra** solo cuando lo confirma un Admin o un Vendedor. El comprador no autogenera órdenes de compra. |
| RN-19 | Al eliminarse, el usuario puede optar por eliminar también sus **pedidos**; los que ya fueron confirmados como **órdenes de compra** son documentos comerciales y no se eliminan. |
| RN-20 | **Slugs para SEO**: cada producto, categoría y etiqueta tiene un slug único que forma parte de su URL pública. |
| RN-21 | **Calificación por estrellas**: cada calificación vale de 1 a 5 estrellas. El promedio visible es `Σ estrellas / cantidad de calificaciones`. El render es fraccional: un promedio de 4.15 pinta 4 estrellas completas y una fracción de la quinta. |
| RN-22 | **Alcance social acotado**: compartir producto: sí. Seguimiento (follow): fuera del MVP. El perfil de usuario es privado; el Vendedor/Admin lo consulta para ver todos sus pedidos y puede editar sus datos de perfil (no rol ni contraseña). |
| RN-23 | **Unidades normalizadas y extensibles**: existe un registro abierto de unidades de venta: unidades, centímetros/metros (cables), kilogramos (cañería/tubería presentada por kilo), etc. Cada producto define su unidad de venta y las cantidades de las líneas de pedido se expresan en esa unidad. Se pueden incorporar unidades nuevas sin rediseño. |
| RN-24 | **Catálogo inicial sembrado**: arranca con dos o tres productos modelo; el resto del catálogo lo crea el staff: Vendedor da de alta productos y etiquetas, Administrador tiene CRUD completo. |
| RN-25 | **Sin moderación en MVP**: no hay flujo de moderación de contenido en esta etapa. |
| RN-26 | **Atributos mínimos del pedido**: líneas (producto + cantidad), precio subtotal, precio total, fecha de creación e id del usuario cliente creador. |
| RN-27 | **Baja de un Vendedor**: sus órdenes de compra confirmadas quedan congeladas con su atribución original; los pedidos sin confirmar son reasignables por un Administrador a otro vendedor activo, con auditoría (ADR-007). |
| RN-28 | **Estados del pedido**: `pendiente de validación` → `aceptado` (genera orden de compra) o `rechazado` (con motivo registrado, visible para el comprador). Solo el pedido pendiente es editable/eliminable por su creador y reasignable entre vendedores (RN-27). El estado `rechazado` es **terminal**: no se edita, pero el comprador puede **duplicarlo como nuevo pedido `pendiente`** editando sus líneas, siempre con el motivo del rechazo a la vista. |
| RN-29 | **Consolidación de pedidos**: un Administrador puede vincular varios pedidos `pendientes` entre sí para emitirlos como **una sola** orden de compra. La OC resultante referencia N pedidos origen; los subtotales se recalculan y el total es la suma. Restricción: **solo pedidos del mismo comprador**, para preservar la atribución (RN-26). Los pedidos consolidados pasan a `aceptado` juntos; ninguno puede consolidarse si ya fue aceptado o rechazado. |
| RN-30 | **Relevancia = más buscados**: el ordenamiento por relevancia rankea por cantidad de búsquedas del producto. La métrica se alimenta con aperturas de detalle cuyo origen es un resultado de búsqueda (no con apariciones en listados: la paginación las inflaría). Acumulado histórico en esta etapa; un eventual decaimiento temporal queda para más adelante. |
| RN-31 | **Ocultar/despublicar productos**: un producto oculto deja de aparecer en catálogo y búsquedas públicas, permanece en base de datos con todas sus relaciones, sigue visible para el staff y puede republicarse. Los documentos históricos que lo referencian no se alteran. |
| RN-32 | **Borrado lógico de productos**: eliminar un producto con historial es una eliminación lógica (`deleted_at`): sale de catálogo y altas nuevas, pero sus referencias históricas (pedidos, órdenes de compra, calificaciones) se resuelven intactas. Nunca hay DELETE físico sobre productos referenciados. |
| RN-33 | **Elegibilidad para calificar**: solo puede calificar un producto quien tenga un **pedido aceptado** (con orden de compra) que incluya ese producto. Evita calificaciones falsas sin relación comercial. |
| RN-34 | **Carrito server-side**: el carrito vive en el servidor asociado al usuario autenticado y sobrevive logout y cambio de dispositivo. El visitante anónimo no arma carrito: el ícono del navbar dispara el prompt de login (UC-A10). |

## Categorías iniciales

Lista semilla cerrada:

`bazar`, `calefacción`, `cerrajería`, `construcción`, `corte`,
`desbaste y pulido`, `electricidad`, `fontanería`, `iluminación`, `gas`,
`herramientas`, `materias primas`, `pintura`, `plomería`,
`refrigeración`, `sanitarios`, `suministros seguridad`, etc.

> La lista puede extenderse por decisión de negocio, pero siempre como
> taxonomía controlada, nunca como entrada libre del usuario final.
