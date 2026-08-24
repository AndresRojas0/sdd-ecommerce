# Diseño de API (REST)

Contratos entre frontends y backend. El estilo es REST (ADR-004) con
superficies separadas por audiencia.

## Estado

Diseño de endpoints **pendiente**: se hará sobre el modelo de dominio ya
espeficado (`domain/domain-model.md`) y las reglas de negocio
(`requirements/business-rules.md`).

## Principios ya decididos

- Un solo backend FastAPI con dos superficies de endpoints:
  - `/api/store/...` → audiencia tienda (pública + comprador autenticado).
  - `/api/admin/...` → audiencia administrador/vendedor, tokens con
    audiencia propia (ADR-005).
- Autenticación por cookies JWT; refresh token rotativo en
  `Path=/auth/refresh` (tienda) y path equivalente propio para admin.
- Errores HTTP consistentes: códigos estándar + cuerpo de error estructurado
  para mapear a los mensajes de login éxito/error (AUTH-05).

## Recursos previstos (borrador de inventario)

`products`, `categories`, `tags`, `units`, `favorites`, `visits`,
`ratings`, `carts`, `orders` (pedidos), `purchase-orders` (órdenes de
compra), `users`, `roles`, `auth`.

> Este documento crecerá con los contratos concretos cuando se especifique
> la fase de diseño de API.
