# Spec: usuarios-vendedores-panel

- **Change ID**: `usuarios-vendedores-panel`
- **Estado**: implementada

## Contexto

El panel solo podía listar/editar-perfil/activar usuarios (A-USR-01..06): el
alta de vendedores, el restablecimiento de contraseñas y el cambio de rol
exigían acceso a base de datos. Se agrega el ciclo de vida completo desde el
panel, con contraseña temporal de un solo uso y primer login forzado.

## Requisitos

| # | Requisito | Fortaleza | Refs |
| - | --------- | --------- | ---- |
| R1 | POST /admin/users crea un usuario con `{email, display_name, role, temp_password?}`; `role` acotado a `comprador|vendedor` (422 con cualquier otro valor); el panel NO crea administradores — el bootstrap por env (BOOT-01/02) es el único camino al rol `administrador` | MUST | A-USR-07, RN-14, ADR-006, UC-AD01 |
| R2 | Email duplicado se rechaza con 422 (unicidad de identidad RN-14); `temp_password` provista que viole la política se rechaza con 422 (AUTH-04) | MUST | A-USR-07, RN-14, AUTH-04 |
| R3 | Si `temp_password` falta, el backend genera una cumpliendo la política (`Tp-` + 8 hex + `!7A`); el nuevo usuario nace `is_active=true` y `must_change_password=true`; la contraseña temporal viaja SOLO en la respuesta de creación (`aviso: "Mostrar una sola vez"`) y nunca se audita ni se vuelve a leer | MUST | A-USR-07, AUTH-04, BOOT-03 |
| R4 | POST /admin/users/{user_id}/password-reset fija una contraseña temporal (provista o generada), activa `must_change_password=true` y revoca TODAS las filas de refresh token del usuario (ambas audiencias); opera sobre cualquier usuario, incluidos otros administradores | MUST | A-USR-08, AUTH-04, ADR-005 |
| R5 | PATCH /admin/users/{user_id}/role cambia el rol solo entre `comprador|vendedor`; un administrador NO puede cambiar su propio rol (422, evitar auto-bloqueo); la operación se audita con estado antes/después del rol | MUST | A-USR-09, RN-27, A-AUD-01 |
| R6 | Los tres endpoints exigen sesión admin-aud con rol `administrador` (token de tienda → 401; vendedor → 403) | MUST | A-USR-07..09, AUTH-10, ADR-005 |
| R7 | Primer login: login con la temporal → 403 `MUST_CHANGE_PASSWORD` con sesión; POST change-password-force con `{current_password, new_password}` → re-login normal (flujo existente, sin cambios) | MUST | BOOT-03, A-AUTH-01, A-AUTH-05 |
| R8 | El panel muestra la contraseña temporal una sola vez con advertencia explícita y botón de copia; el alta/reset/cambio de rol desde la UI usa los endpoints R1/R4/R5 | SHOULD | A-USR-07..09, UC-AD01 |

## Escenarios

### E1 — Alta de vendedor con temporal automática

- **Given** un administrador autenticado en la superficie admin y un email no registrado
- **When** POST /admin/users con `{email, display_name, role: "vendedor"}` sin `temp_password`
- **Then** responde 201 con `user.must_change_password=true`, `user.is_active=true`, `temp_password` (>= 8 chars, política AUTH-04) y `aviso: "Mostrar una sola vez"`; queda fila en `staff_audits` con `accion="usuario.crear"` y `datos_despues={email, role}` sin la contraseña

### E2 — Primer login forzado

- **Given** el usuario creado en E1 con su contraseña temporal
- **When** POST /admin/auth/login con la temporal → 403 `MUST_CHANGE_PASSWORD` con cookies admin; POST /admin/auth/change-password-force con `{current_password: temporal, new_password: nueva}`; re-login
- **Then** el cambio-force responde 200 y revoca los refresh del usuario; la temporal ya no sirve (401) y el re-login entrega sesión válida con `role=vendedor` en /admin/auth/me

### E3 — Reset de contraseña revoca sesiones

- **Given** un usuario con sesión activa (filas de refresh vivas) en cualquier audiencia
- **When** un administrador hace POST /admin/users/{id}/password-reset
- **Then** todas sus filas de refresh quedan `revoked=true`, la contraseña anterior deja de autenticar (401) y la temporal entregada fuerza `MUST_CHANGE_PASSWORD` en el próximo login

### E4 — Cambio de rol auditado con guard de auto-bloqueo

- **Given** un administrador y un usuario con rol `comprador`
- **When** PATCH /admin/users/{id}/role con `{role: "vendedor"}`
- **Then** responde 200 con el rol nuevo y queda fila en `staff_audits` con `accion="usuario.cambiar_rol"` y `datos_antes/datos_despues` del rol; si el objetivo es el PROPIO usuario del admin, 422; `role=administrador` → 422

### E5 — Gates de audiencia y rol

- **Given** un token de tienda (comprador) y un token admin-aud de vendedor
- **When** invocan cualquiera de los tres endpoints nuevos
- **Then** token de tienda → 401; vendedor (admin-aud) → 403; solo `administrador` (admin-aud) opera

## Impacto

- **Endpoints**: nuevos A-USR-07 (`POST /admin/users`), A-USR-08
  (`POST /admin/users/{user_id}/password-reset`), A-USR-09
  (`PATCH /admin/users/{user_id}/role`); sin endpoints modificados.
- **Esquema + migración**: sin cambios de tablas — `users`,
  `refresh_tokens` y `staff_audits` ya soportan el flujo
  (`must_change_password`, `revoked`, append-only). Sin revisión Alembic nueva.
- **Docs a actualizar**: `architecture/01-api-design.md` (§4, §7.1),
  `testing/01-test-cases.md` (TC-USR-01..03), `planning/03-changelog.md`.

## Criterios de verificación

| Criterio | TC | Estado |
| -------- | -- | ------ |
| Alta de vendedor con temporal automática + primer login forzado | TC-USR-01 (suite: `test_admin_user_lifecycle.py`) | verificado |
| Reset revoca refresh de ambas audiencias y mata la contraseña vieja | TC-USR-02 (suite: `test_admin_user_lifecycle.py`) | verificado |
| Cambio de rol auditado con guard de auto-bloqueo | TC-USR-03 (suite: `test_admin_user_lifecycle.py`) | verificado |
| Gates 401/403 por audiencia y rol en los tres endpoints | TC-AUTH10-02 | verificado |
