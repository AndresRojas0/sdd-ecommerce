# Roadmap

Evolución planificada (hipótesis, se revisa en cada milestone):

- **Iteración 1 — MVP base (completada)**: auth con JWT cookies (ADR-003),
  catálogo público (búsqueda/filtros/ordenamientos RN-07), carrito por
  usuario (RN-34), favoritos, visitas anónimas (ADR-001), 37 tests backend.
- **Iteración 2 — Flujo comercial (completada)**: pedidos + máquina de estados
  RN-28, reserva/confirmación/devolución de stock RN-35, órdenes de compra
  RN-29 y facturas RN-36, kanban de pedidos y dashboard totales-hoy (RN-37)
  en admin. Implementada (`efb8b2f`, `5b88821`).
- **Iteración 3 — Panel admin completo (en curso)**: gestión de usuarios y
  vendedores (UC-AD01..24), auditoría de staff (A-AUD-01) y descuentos según
  ADR-008 (A-PROD-08/09). Categorías árbol 2 niveles y colecciones ya
  implementadas (`ae0090d`, `a70bac1`, RN-38/39).
- **Post-MVP (fuera de alcance inmediato)**: imágenes de producto (RN-13),
  avatar (UC-C07), recuperación de contraseña (RF-17), E2E con Playwright,
  producción en VPS (`architecture/03-deployment.md`), escalado
  multi-instancia + Redis (rate limiting).
