# Requirements

Define qué debe hacer el sistema: reglas de negocio, funcionalidades,
restricciones y comportamientos esperados.

---
## Documentos esperados

| Archivo | Qué contiene |
| ------- | ------------ |
| `business-rules.md` | Reglas que gobiernan el comportamiento del sistema. |
| `functional-requirements.md` | Funcionalidades que debe ofrecer la aplicación. |
| `non-functional-requirements.md` | Calidad, rendimiento, seguridad, restricciones. |
| `authentication.md` | Especificación de autenticación y autorización. |
| `user-stories.md` | Necesidades expresadas desde la perspectiva del usuario. |

> Requisitos no funcionales: cubiertos en `architecture/02-security.md` y `architecture/03-deployment.md`. `user-stories.md`: retirado — los casos de uso (`use-cases/`) cumplen ese rol.

## Consejos

- Las reglas de negocio son la fuente de verdad para los casos de prueba.
- Cada requisito funcional debería poder rastrearse hasta su implementación.

