# ADR-003 — Autenticación con JWT en cookies y admin como aplicación separada

## Contexto

El sistema de login se basa en JWT. Las credenciales viajan en cookies.
La recomendación de expiración/refresh quedó delegada. Además, el panel
de Administración será **otro proyecto separado** que consume la misma
base de datos pero con su propio sistema de login y cookies, distinto al
del frontend. El stack tecnológico concreto se definirá más adelante.

## Decisión

### Frontend (tienda)

- **Access token JWT**: vida corta, **15 minutos**. Claims mínimos: `sub`
  (userId), `role`, `iat`, `exp`. Stateless: el backend no consulta DB por
  request.
- **Refresh token**: obligatorio, **30 días**, **rotativo**: cada uso emite
  uno nuevo y revoca el anterior; se persiste hasheado para poder
  revocarlo y detectar reuso (si un refresh ya usado vuelve a aparecer,
  se invalida toda la familia).
- **Cookies**: ambos tokens viajan en cookies `HttpOnly` (inaccesibles a
  JavaScript → mitiga XSS), `Secure` (solo HTTPS) y `SameSite=Lax`
  (mitigación CSRF razonable para navegación mobile-first). La cookie del
  refresh token se limita con `Path=/auth/refresh`.
- Expiración tipo redes sociales: sesión larga vía refresh rotativo de
  30 días; logout = revocación de la familia de refresh tokens.

### Panel de administración (proyecto separado)

- Aplicación independiente que accede a la **misma base de datos**.
- Sistema de login y cookies **propios y aislados**: nombres de cookie,
  secreto/audiencia JWT y paths distintos a los del frontend. Un token del
  frontend no es válido en el admin y viceversa.

## Alternativas

| Alternativa | Por qué se descarta |
| ----------- | ------------------- |
| Tokens en localStorage | Vulnerable a XSS: cualquier script lee las credenciales. |
| Access token de vida larga sin refresh | No permite revocación ni expiración segura de sesiones comprometidas. |
| Sesiones server-side tradicionales | Válida, pero se eligió JWT stateless para escalar el frontend sin estado de sesión compartido. |
| Admin dentro del mismo frontend con roles | Mezcla superficies de ataque y acopla releases internos con la tienda pública. |

## Consecuencias

- Positivas: credenciales inaccesibles desde JS; revocación real vía refresh rotativo; despliegue y evolución independientes de tienda y admin.
- Negativas: requiere manejar rotación/detección de reuso correctamente; dos sistemas de sesión que mantener; CSRF exige SameSite correcto y validación adicional en mutaciones sensibles.
- Pendiente: definir stack concreto (otro día, según decisión del proyecto).
