# Casos de uso — Administrador

> **Estado: definición aparte.** La parte administrativa es otro proyecto
> (ADR-005); sus casos de uso se especificarán en el repositorio/documentación
> del panel de administración. Este documento reserva el alcance mínimo que
> el backend de este proyecto debe soportar.

## Áreas previstas para revisión conjunta

| Área | Capacidades mínimas que el backend expondrá |
| ---- | ------------------------------------------- |
| Gestión de usuarios y roles | Asignar/revocar rol Vendedor y Administrador; reactivar cuentas dadas de baja; ver estado `is_active`. |
| Catálogo | CRUD completo de productos, categorías, etiquetas y unidades (RN-01, RN-24). |
| Pedidos | Confirmar pedido → orden de compra; reasignación de pedidos pendientes entre vendedores activos. |
| Configuración | Ventana de deduplicación de visitas (ADR-001), parámetros de sesión. |
| Auditoría | Registro de acciones staff (pendiente en `architecture/02-security.md`). |

## Bootstrap

El primer administrador no surge de un caso de uso sino del bootstrap por
variables de entorno con cambio forzado de contraseña (ADR-006).
