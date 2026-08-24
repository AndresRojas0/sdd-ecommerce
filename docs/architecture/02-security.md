# Modelo de seguridad

Autenticación, autorización y protección de datos (primera iteración).

## Autenticación

Dos sistemas **independientes** sobre el mismo backend:

| Superficie | Mecanismo | Detalle |
| ---------- | --------- | ------- |
| Tienda pública | JWT en cookies | Access 15 min + refresh rotativo 30 días; cookies `HttpOnly`, `Secure`, `SameSite=Lax`; refresh con `Path=/auth/refresh` (ADR-003). |
| Panel admin | JWT en cookies propios | Secret y audiencia distintos; credenciales iniciales por bootstrap de env (ADR-006) con cambio forzado en primer login (BOOT-03). |

- Los refresh tokens se persisten **hasheados** para permitir revocación y
  detección de reuso.
- Contraseñas: solo hash (RN-15); política mínima 8 caracteres, una
  mayúscula, un número y un caracter especial.

## Autorización (RBAC)

| Rol | Alcance |
| --- | ------- |
| Visitante anónimo | Lectura del catálogo público. |
| Comprador | Favoritos, carrito/pedidos, calificaciones sobre sus propios recursos. |
| Vendedor | Lectura de pedidos, alta de pedidos por cliente, alta de productos/etiquetas, consulta de perfiles de compradores. |
| Administrador | CRUD total + confirmación de pedidos + gestión de usuarios/roles. |

Reglas transversales: propiedad de recursos (un comprador solo ve/edita SUS
favoritos, pedidos y calificaciones), perfil de usuario privado (RN-22),
baja lógica sin borrado físico (RN-17).

## Protección de datos

- Cookies firmadas por el backend; nada sensible legible desde JS.
- Validación server-side de toda entrada (Pydantic).
- CSRF: `SameSite=Lax` + validación adicional en mutaciones sensibles.
- Secretos por variables de entorno fuera del repositorio (`.env` ignorado
  por Git).

## Pendientes

- Rate limiting de endpoints públicos (búsqueda, login).
- Auditoría de acciones del staff (confirmación de pedidos, altas de catálogo).
