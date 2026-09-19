# Verificación: diseño de API vs. código implementado

Fecha: 2026-09-16.

## Alcance

Comparación entre los 83 endpoints diseñados en `01-api-design.md` y las 81
rutas reales del backend (18 routers, sin prefijo `/api`).

## Resultado

**68 de 83** endpoints diseñados están implementados (mapeo S-\*/A-\* → rutas
reales; las diferencias de naming son cosméticas: `accept`/`aceptar`,
`duplicate`/`duplicar`, `reassign`/`vendedor`, `PUT` vs `PATCH`,
`visibility`/`publicacion`).

**15 diseñados sin código**: A-AUTH-01..04, A-USR-03/05/06, A-PROD-08/09
(ADR-008, esperado), A-COL-06, A-PED-06, A-STK-03, A-FAC-01/02, A-AUD-01.

**15 rutas de código sin entrada en el diseño**: `/health` y `/healthz`,
`/auth/change-password-force`, `GET /users/me` (duplicado de S-AUTH-05),
`PUT /users/me/avatar` (¡contradice §8.4 que difiere el avatar!), dos
variantes extra de reactivación, `GET /categorias/{identifier}`,
`/etiquetas/autocomplete`, `DELETE /etiquetas/{id}`,
`DELETE /unidades-medida/{id}`, `DELETE /carts/me`, `GET` y `DELETE` de
ratings, `PUT /admin/stock/{product_id}` (ajuste manual — el diseño lo
declara fuera de MVP).

## Hallazgo crítico

El aislamiento de audiencias (ADR-003/005) **NO está implementado**: no
existe `/admin/auth/*` ni superficies `/api/store` vs `/api/admin`; tienda y
admin comparten `/auth/*` distinguiendo por rol (`require_role`). El
TC-AUTH10-01 (token de tienda rechazado en admin y viceversa) no es
ejecutable tal como está escrito. Esto es una decisión de arquitectura
pendiente, no drift cosmético.

RESUELTO: superficie `/admin/auth/*` implementada con `aud=admin`, secreto y
cookies propios; barrido de audiencia en todos los endpoints admin (55 tests
en verde).

## Acciones

| Acción | Estado |
| ------ | ------ |
| Decidir aislamiento de audiencias (implementar superficies separadas o revisar ADR-003/005). | Hecha (aislamiento implementado; suite 55 tests). |
| Al decidir, actualizar `01-api-design.md` con las rutas reales o alinear el código. | Hecha (aislamiento implementado; suite 55 tests). |
| Incorporar al diseño o retirar del código los drifts menores (avatar, stock manual, ratings GET/DELETE, clear cart, variantes de reactivación). | Pendiente. |

## Seguimiento

`docs/planning/02-open-questions.md`.
