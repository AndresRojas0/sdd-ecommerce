# Preguntas abiertas

| # | Pregunta | Dónde se discute | Estado |
| - | -------- | ---------------- | ------ |
| 1 | Superficie del Vendedor: asumida `/api/admin` (ADR-005), a confirmar explícitamente. | `use-cases/vendedor.md`; `01-api-design.md` §8.6 | Abierta |
| 2 | Alcance de rechazo del Vendedor: `vendedor.md` dice `* → rechazado`; RN-28 solo permite desde `pendiente`/`aceptado`. | `01-api-design.md` §9.3 | Abierta — ajustar doc o regla |
| 3 | Actor "Logística" sin rol en `users.role`; transiciones mapeadas a administrador. | `01-api-design.md` §9.2 | Abierta — definir actor si hace falta |
| 4 | Avatar de usuario: RF-28/UC-C07 vs `users.avatar` "nulo en MVP". | `01-api-design.md` §9.4 | Abierta |
| 5 | Dominio de producción y DNS. | `03-deployment.md` | Abierta — decisión del mantenedor; bloquea M7 |
| 6 | Estrategia E2E con Playwright. | `testing/00-strategy.md` | Diferida — cuando la app SvelteKit esté estable |
| 7 | UC-AD06 con ID colisionado en `administrador.md` (productos vs árbol de categorías). | `01-api-design.md` §9.1 | Abierta — limpieza documental |

## Cerradas (historial)

| Pregunta | Resolución |
| -------- | ---------- |
| Mecánica de descuentos (% vs. precio final, vigencia) | ADR-008 |
| Rate limiting y auditoría de staff | `02-security.md` |
| CI/CD, migraciones, producción | `03-deployment.md` |
| Diseño de endpoints | `01-api-design.md` |
