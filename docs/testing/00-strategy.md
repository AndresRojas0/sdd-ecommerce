# Estrategia de pruebas

Cómo se prueba el sistema. Prioridad del MVP: **backend** (FastAPI).

## Niveles

| Nivel | Qué prueba | Herramientas |
| ----- | ---------- | ------------ |
| **Unitarias** | Lógica de negocio pura: validaciones, cálculos (subtotales/totales RN-26/RN-29), política de contraseña (RN-15), promedio fraccional (RN-21), generación de slugs (RN-20), scoring de relevancia (RN-30) | `pytest` |
| **De API/endpoint** | Cada endpoint importante: contrato REST, códigos HTTP, autorización por rol/audiencia, efectos en DB | `pytest` + cliente ASGI (`httpx.AsyncClient` / `TestClient`) |
| **De integración** | Flujos completos multi-endpoint: carrito→pedido→aceptación→OC, consolidación, baja/reactivación | ídem |

> Nota de terminología: probar un endpoint implica levantar la app y pasar
> por HTTP: técnicamente son pruebas de integración dirigidas. Las
> unitarias puras quedan para la lógica extraída a servicios/esquemas. La
> estrategia cubre ambas capas.

## Definición: endpoint "importante"

Se considera **obligatorio testear** todo endpoint que:

1. Mute estado (POST/PUT/PATCH/DELETE), o
2. Ejecute una regla de negocio en su lectura (búsqueda combinable,
   ordenamientos, estadísticas), o
3. Pertenezca a autenticación/autorización.

En la práctica esto cubre: `/auth` completo (incluye refresh rotativo,
cambio de contraseña, reactivación), carrito, pedidos y su ciclo de vida,
consolidación, calificaciones (elegibilidad RN-33), favoritos con
contadores, visitas con deduplicación (RN-08), ABM de productos/categorías/
tags/unidades, gestión de usuarios/vendedores y bootstrap de admin (ADR-006).

## Infraestructura

| Aspecto | Decisión |
| ------- | -------- |
| Base de datos de pruebas | **PostgreSQL real** en contenedor Podman (no SQLite: las restricciones N:M y constraints difieren). Imagen desde `public.ecr.aws`, coherente con ADR-004 |
| Aislamiento | Una transacción por test con rollback, o truncado por fixture; sin dependencia de orden |
| Seeds | Catálogo modelo (2–3 productos, RF-24) + categorías/tags semilla como fixtures compartidos |
| Bootstrap admin en tests | Caso aparte: verificar idempotencia y cambio forzado (BOOT-01..04) con env vars de test |

## Reglas de calidad

| ID | Regla |
| -- | ----- |
| TEST-01 | **Toda regla de negocio (RN-xx) debe tener al menos un caso happy y uno bad path** referenciándola por ID. |
| TEST-02 | Todo caso de uso con flujos alternativos (AUTH-05, UC-B06a, UC-AD19...) tiene su test de flujo alternativo. |
| TEST-03 | Los tests viven junto al backend y corren en local con un solo comando (`pytest`). |
| TEST-04 | Un endpoint no se considera terminado sin sus pruebas: vale para el Definition of Done de cada change. |
| TEST-05 | Cobertura objetivo: ≥90% en dominio y auth; 100% de las RN con test asociado (TEST-01). |

## Pendientes

- Pipeline CI que ejecute la suite (herramienta por definir, ver
  `architecture/03-deployment.md`).
- Estrategia de frontend (E2E con Playwright es candidato natural): se
  definirá cuando exista la app SvelteKit.
