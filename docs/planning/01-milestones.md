# Milestones

Cada hito tiene un objetivo verificable: el criterio indica qué tests/TCs lo
prueban.

| Hito | Objetivo verificable | Estado |
| ---- | -------------------- | ------ |
| M1 — Infra + auth | `podman-compose up --build` levanta db/api/web/admin con `/health` OK; auth con JWT cookies y refresh rotativo (ADR-003); suite backend en verde (`PYTHONPATH=backend pytest -q`). | Completado |
| M2 — Catálogo público | CRUD de staff sobre productos/categorías/etiquetas; búsqueda + filtros + ordenamientos RN-07; visitas anónimas con dedup (RN-08/ADR-001). Cubierto por tests de products/visits. | Completado |
| M3 — Carrito + favoritos | Carrito único server-side por usuario (RN-34), counters de guardados (RN-09), preview antes de generar el pedido (RN-12). Cubierto por tests de cart. | Completado |
| M4 — Pedidos → OC → factura | Transiciones RN-28 con efectos de stock (RN-35), consolidación de pedidos del mismo comprador (RN-29), facturación con `numero_fiscal` único (RN-36), kanban en admin. Endpoints A-PED-*/A-OC-*/A-STK-*/A-FAC-*/A-DASH-01 implementados con sus TCs. | Completado (`efb8b2f`) |
| M5 — Admin completo | Gestión de usuarios y vendedores (UC-AD01..24), categorías/colecciones (UC-AD29..34), métricas y auditoría de staff (A-AUD-01) operativas en el panel. Categorías/colecciones implementadas (`ae0090d`, `a70bac1`); resto pendiente. | Parcial |
| M6 — Descuentos | Columnas y mecánica de ADR-008; endpoints A-PROD-08/09; sort `con_descuento` activo; snapshots `precio_lista` en `pedido_items`. | Pendiente |
| M7 — Producción | VPS con podman rootless + Caddy + TLS; `deploy.yml` con CI deploy y `alembic upgrade head`; backups `pg_dump` + rclone. Requiere dominio definido. | Pendiente (bloqueado por dominio) |
