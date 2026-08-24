# Casos de uso — Cuenta (común a Comprador y Vendedor)

Casos de uso de autogestión de cuenta, compartidos por todo usuario
autenticado. Aplican también al Vendedor salvo indicación contraria.

| ID | Caso de uso | Notas |
| -- | ----------- | ----- |
| UC-C01 | Registrarse | Crea cuenta base **Comprador** con email único + display-name + contraseña (RN-14/RN-15). El rol Vendedor/Admin no se autorga: lo asigna un Administrador. |
| UC-C02 | Iniciar sesión | Email + contraseña; mensaje de éxito o error específico (AUTH-05); registra `last_login_at`. |
| UC-C03 | Cerrar sesión | Revoca la familia de refresh tokens. |
| UC-C04 | Recuperar contraseña | **Diferida**: requiere envío de correos (AUTH-06). Queda especificado, no implementado en MVP. |
| UC-C05 | Cambiar contraseña (logueado) | Pide contraseña actual + nueva (RN-15). Al confirmar, invalida todos los refresh tokens activos por seguridad. Distinto de UC-C04: no necesita email. |
| UC-C06 | Editar perfil | Modifica display-name y otros datos del perfil. |
| UC-C07 | Cambiar avatar | Carga/actualiza la imagen de avatar. |
| UC-C08 | Consultar su perfil | Ve sus propios datos (el perfil es privado para terceros, RN-22). |
| UC-C09 | Darse de baja | Baja lógica `is_active = false` (RN-17): conserva visitas, favoritos y pedidos. Ofrece decidir qué hacer con sus pedidos (RN-19). |
| UC-C10 | Reactivar cuenta | Si un usuario dado de baja inicia sesión con credenciales válidas, el sistema ofrece reactivar: `is_active = true`, mismo userId, historial íntegro (ADR-002). |

## Flujos alternativos

- **UC-C02**: credenciales inválidas → error específico sin revelar si existe
  el email. Cuenta dada de baja → se ofrece UC-C10.
- **UC-C05**: contraseña actual incorrecta → no se cambia; nueva inválida
  según RN-15 → rechazo con detalle de política.

## Reactivación y administradores

Un Administrador puede además reactivar manualmente una cuenta dada de baja
(mismo efecto que UC-C10).
