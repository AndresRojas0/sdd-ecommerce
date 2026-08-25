# ADR-005 — Panel de administración como aplicación Svelte independiente que consume la API

## Contexto

ADR-003 definió originalmente el admin como proyecto separado que consumía
**la conexión a la base de datos** directamente. Al definirse el stack
(ADR-004) se resolvió que el backend FastAPI es la única puerta de datos y
que el admin es también una aplicación Svelte. Este ADR registra esa
evolución y **supersede parcialmente** a ADR-003 en lo referente al acceso
del admin a los datos.

## Decisión

- El panel de administración es un **proyecto independiente en SvelteKit**
  (evolución del redactado original "Svelte SPA pura": se implementa con el
  mismo framework que el storefront para compartir patrones).
- Consume el **backend FastAPI vía REST**: nunca accede directo a
  PostgreSQL.
- Su sistema de autenticación es **independiente** del de la tienda:
  credenciales, cookies, secreto y audiencia JWT propios. Un token del
  frontend no autoriza endpoints de admin ni viceversa.
- El backend distingue ambas audiencias (`aud` / `scope` del token) y expone
  superficies de endpoints separadas.

## Alternativas

| Alternativa | Por qué se descarta |
| ----------- | ------------------- |
| Admin accediendo directo a la base de datos (ADR-003 original) | Duplica lógica de negocio, salta validaciones del backend y amplía la superficie de seguridad. |
| Admin dentro del frontend público con roles | Acopla releases internos con la tienda y mezcla superficies de ataque. |
| Herramienta tipo admin generator sobre la DB | Control insuficiente sobre reglas de negocio (confirmación de pedidos, etc.). |

## Consecuencias

- Positivas: toda regla de negocio vive en el backend; despliegue y evolución independientes; superficie admin auditable y aislable (red, paths, tokens).
- Negativas: requiere diseñar contratos REST específicos para admin; dos frontends que mantener.

## Relación con otros ADRs

- Supersede parcial de **ADR-003** (acceso a datos del admin).
- Complementa a **ADR-004** (stack) y **ADR-006** (bootstrap de credenciales).
