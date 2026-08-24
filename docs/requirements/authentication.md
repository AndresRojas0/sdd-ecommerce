# Autenticación y autorización

Especificación de roles, autenticación y autorización (tercera iteración).

## Actores y roles

| Rol | Denominación | Capacidades |
| --- | ------------ | ----------- |
| Visitante anónimo | Usuario no autenticado | Consultar el catálogo: ver productos, buscar, filtrar y ordenar. El catálogo es **público**. No puede favoritar, pedir ni calificar. |
| Comprador | Usuario registrado | Todo lo del visitante + gestionar favoritos, armar carrito, generar pedidos y calificar productos. Puede darse de baja (baja lógica). |
| Vendedor *(alias: atención al público / ventas)* | Rol operativo | Ver pedidos generados y su estado; cargar pedidos en nombre de un cliente; dar de alta productos y sus etiquetas en el catálogo (RN-24); consultar el perfil de un usuario y todos sus pedidos (RN-22). |
| Administrador | Rol de administración | **Alcance total**: ABM de productos, categorías, etiquetas, usuarios, roles, confirmación de pedidos y configuración general del sistema. |

## Identidad del usuario

| Atributo | Descripción |
| -------- | ----------- |
| `email` | Identificador único del usuario. Se usa para el login. |
| `display_name` | Nombre visible en la plataforma. |
| `avatar` | Imagen de perfil del usuario. |
| `password` | Contraseña con política mínima (RN-15). Se almacena solo como hash. |
| `created_at` | Fecha de creación del perfil. |
| `last_login_at` | Fecha y hora del último login exitoso. |
| `is_active` | Baja lógica: `false` = usuario dado de baja (RN-17). |

## Reglas

| ID | Regla |
| -- | ----- |
| AUTH-01 | El acceso a favoritos, carrito, pedidos y calificaciones requiere sesión iniciada. |
| AUTH-02 | La consulta pública del catálogo no requiere autenticación. |
| AUTH-03 | El login se realiza con `email` + contraseña. El `email` es único por cuenta. |
| AUTH-04 | Política de contraseña: mínimo 8 caracteres, al menos una mayúscula, un número y un caracter especial. |
| AUTH-05 | Login muestra confirmación de éxito o mensaje de error específico ante credenciales inválidas u otros problemas de autenticación (happy path / bad path). |
| AUTH-06 | Recuperación de contraseña prevista, pero diferida: no hay envío de correos electrónicos configurado en esta etapa. |
| AUTH-07 | La baja del usuario es lógica (`is_active = false`); conserva visitas, favoritos y pedidos (RN-17). |
| AUTH-08 | Solo Admin o Vendedor confirma un pedido y genera la orden de compra (RN-18). |
| AUTH-09 | El login del frontend se basa en **JWT con credenciales en cookies**: access token 15 min + refresh token rotativo 30 días, cookies `HttpOnly`, `Secure`, `SameSite=Lax`. Detalles y alternativas: `decisions/ADR-003-jwt-cookies-y-admin-separado.md`. |
| AUTH-10 | El panel de Administración es un **proyecto Svelte independiente** que consume la API REST del backend; su sistema de login y cookies es propio y aislado del frontend de tienda (ADR-005). |
| AUTH-11 | Bootstrap del admin: en el primer arranque el backend crea el administrador inicial desde `ADMIN_INITIAL_*` (env) y **fuerza el cambio de contraseña en el primer login** (ADR-006, BOOT-01..04). |
| AUTH-12 | El Administrador activa/desactiva cuentas de usuarios y vendedores (toggle `is_active`); la desactivación impuesta sigue las reglas de baja lógica (RN-17) y de reactivación (UC-C10). |
