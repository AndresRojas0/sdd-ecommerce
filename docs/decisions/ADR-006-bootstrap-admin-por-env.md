# ADR-006 — Bootstrap del usuario administrador por variables de entorno

## Contexto

El sistema necesita al menos un usuario administrador para operar
(catalogo, roles, confirmación de pedidos). El punto real de decisión no es
"si hay que sembrar un admin" sino **cómo se generan sus credenciales
iniciales** en un despliegue desde cero (contenedores, bootcamp).

## Decisión

**Setup por variable de entorno**: en el primer arranque, el backend detecta
que no existe ningún administrador y crea el usuario inicial leyendo:

- `ADMIN_INITIAL_EMAIL`
- `ADMIN_INITIAL_PASSWORD`
- `ADMIN_INITIAL_DISPLAY_NAME` (opcional)

Reglas del bootstrap:

| ID | Regla |
| -- | ----- |
| BOOT-01 | Solo corre si NO existe ningún usuario administrador; en arranques siguientes es un no-op (idempotente). |
| BOOT-02 | La contraseña inicial debe cumplir la política general (RN-15); si no, el arranque falla ruidosamente. |
| BOOT-03 | El admin creado tiene `must_change_password = true`: el sistema **fuerza el cambio de contraseña en el primer login** antes de permitir cualquier otra operación. |
| BOOT-04 | Las variables de entorno no se usan como almacenamiento persistente de credenciales: después del primer login forzado, la única contraseña válida es la nueva. |

> Resolución posterior (no cambia la decisión): la variable de email se
> denomina `ADMIN_INITIAL_USER` (antes redactada como `ADMIN_INITIAL_EMAIL`);
> la semántica es idéntica. Implementación: `backend/app/core/bootstrap.py`,
> ejecutado idempotentemente al arranque de la API; tabla `users` provisional
> gestionada con create_all hasta que Alembic tome el control del esquema.

## Alternativas

| Alternativa | Por qué se descarta |
| ----------- | ------------------- |
| Comando CLI de seed manual | Requiere paso manual extra por ambiente; fácil de olvidar o ejecutar dos veces. |
| Invitación por email | Bloqueada: no hay envío de correos en esta etapa (AUTH-06). |
| Admin hardcodeado en código | Credenciales en repositorio: riesgo de seguridad inaceptable. |

## Consecuencias

- Positivas: simple; reproducible y scriptable en contenedores; ideal para entornos de bootcamp/demos; sin secretos en código.
- Negativas: las credenciales iniciales transitan por variables de entorno (restringir acceso a `.env`/orquestador); depende de que BOOT-03 se implemente correctamente para eliminar la ventana de credenciales conocidas.
