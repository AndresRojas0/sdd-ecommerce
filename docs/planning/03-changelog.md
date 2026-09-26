# Changelog documental

Historial de cambios de DOCUMENTOS por fecha (bootstrap desde `git log`).
El changelog no registra código: eso vive en git.

| Fecha | Cambio | Commit |
| ----- | ------ | ------ |
| — | Bootstrap de la documentación SDD: visión, requisitos, dominio, UI, casos de uso, ADRs, testing. | — ¹ |
| — | Auditoría documental (revisión de los 47 documentos). | — ¹ |
| 2026-09-16 | Diseño de 80 endpoints REST + binding de 32 TCs. | `8ab671f` |
| 2026-09-16 | Resolución de decisiones abiertas: ADR-008, rate limiting, auditoría de staff, CI/CD, migraciones, producción. | `f83a167` |
| 2026-09-16 | Materialización de carpetas andamio (planning/specs/reviews). | este commit |
| 2026-09-25 | M7 producción: API en FastAPI Cloud + Supabase (pooler us-east-1), admin bootstrap, tienda y panel en Vercel con rewrites same-origin (cookies first-party); alias /api para colisiones /categorias y /colecciones del panel | `953d0fc`/`9d946bc` |
| 2026-09-16 | M6 descuentos (ADR-008) implementado + reconciliación de diseño de API + TCs nuevos. | `36ed99b` / este change |
| 2026-09-19 | M5: últimos 9 endpoints admin sin código (A-USR-03/05/06, A-COL-06, A-PED-06, A-STK-03, A-FAC-01/02, A-AUD-01) + tabla `staff_audits` append-only (migración 006) e instrumentación de auditoría; docs de API/TCs reconciliados. | este change |
| 2026-09-25 | Ciclo de vida de usuarios desde el panel: alta con contraseña temporal y primer login forzado (A-USR-07), reset con revocación de sesiones (A-USR-08), cambio de rol con guard de auto-bloqueo (A-USR-09); delta spec `specs/usuarios-vendedores-panel.md`, TC-USR-01..03, UI del panel (usuarios + vendedores). | este change |

¹ Commits previos a la ventana de 20 del `git log` usada para el bootstrap.
