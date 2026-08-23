# Visión

## Problema

Los catálogos de ferretería y suministros industriales son amplios y
heterogéneos: miles de productos (tornillos, discos, llaves, cables,
materias primas, etc.) que se agrupan por familias técnicas y se
describen con especificaciones propias de cada rubro. Encontrar el
producto correcto exige poder buscar por nombre, por familia o por sus
atributos técnicos.

## Solución

Una aplicación ecommerce donde un usuario registrado puede:

- consultar el catálogo de productos,
- buscar productos por categoría, por nombre o por especificaciones técnicas,
- filtrar productos por categoría y por etiquetas (tags),
- guardar productos como favoritos,
- generar pedidos de productos,
- calificar productos.

## Usuarios

| Actor | Descripción |
| ----- | ----------- |
| Visitante anónimo | Consulta el catálogo público sin registrarse. |
| Comprador | Usuario registrado que consulta, busca, favorita, pide y califica productos. |
| Vendedor | Staff que ve pedidos, carga pedidos por clientes y da de alta productos y etiquetas. |
| Administrador | Alcance total sobre el sistema. |

## Plataforma

**Mobile-first**: la experiencia se diseña primero para dispositivos móviles
y luego se escala a pantallas mayores.

## Principio rector

La organización del catálogo combina dos mecanismos complementarios:

- **Categorías**: taxonomía **cerrada**, controlada por el sistema; un
  producto puede pertenecer a una o más.
- **Etiquetas (tags)**: vocabulario **abierto**, dinámico, con
  autocompletado mientras el usuario escribe.

Todo término navegable (producto, categoría, etiqueta) expone un slug para
URLs amigables y SEO.
