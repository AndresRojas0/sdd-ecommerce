# ADR-007 — Destino de los pedidos ante la baja de un Vendedor

## Contexto

El rol Vendedor confirma pedidos y genera órdenes de compra, y además puede
darse de baja (baja lógica, RN-17). Al ocurrir eso queda la pregunta de qué
sucede con los documentos asociados a su gestión. El punto real de decisión
es si la atribución histórica se conserva o se transfere.

## Decisión

Criterio **híbrido** según el estado del documento:

| Documento | Al darse de baja el vendedor | Transferencia |
| --------- | ---------------------------- | ------------- |
| **Orden de compra ya confirmada** | Queda **congelada** con su vendedor original como atribución histórica. Es un documento comercial emitido: no cambia de autor. | Nunca. |
| **Pedido aún sin confirmar** | Queda operativo y es **reasignable** por un Administrador a otro Vendedor activo para su seguimiento y confirmación. | Sí, por Admin, con registro de auditoría (quién, cuándo, desde qué vendedor). |

Esto se formaliza como regla de negocio **RN-27** y habilita el caso de uso
de administración "Reasignar pedido pendiente entre vendedores activos".

## Alternativas

| Alternativa | Por qué se descarta |
| ----------- | ------------------- |
| Todo permanece con el vendedor original | Simple, pero los pedidos pendientes quedan huérfanos operativamente: nadie activo los confirma. |
| Transferencia total (incluidas órdenes confirmadas) | Rompe la atribución histórica del documento comercial emitido; pierde valor de auditoría. |

## Consecuencias

- Positivas: trazabilidad comercial intacta; ningún pedido pendiente queda sin responsable activo; transferencias acotadas y auditables.
- Negativas: requiere modelo con `vendedor_id` histórico en la orden de compra y `vendedor_asignado` actualizable en el pedido; pantalla admin de reasignación.
