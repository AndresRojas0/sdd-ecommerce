# ADR-001 — Conteo de visitas de producto con usuarios anónimos

## Contexto

El catálogo es público: cualquier visitante, autenticado o no, puede abrir
el detalle de un producto. Cada apertura del detalle cuenta como una
**visita**. Se necesita un contador de visitas por producto que no se
inflame con recargas de página (F5 no debe incrementar más de una vez).

## Decisión

Identificar al **visitante** (autenticado o anónimo) mediante un
identificador estable:

- Usuario autenticado → su `userId`.
- Visitante anónimo → cookie propia de primera partida (*UUID*) emitida al
  primer acceso, independiente de la sesión.

El servidor registra `(producto, visitante, marca_de_tiempo)` y computa
una visita nueva solo si no existe registro previo del mismo visitante
para ese producto dentro de una **ventana de deduplicación** (propuesta:
24 horas). F5 dentro de la ventana no incrementa el contador; fuera de la
ventana, sí.

El conteo se persiste como total agregado por producto, conservando el
detalle mínimo necesario para aplicar la ventana.

## Alternativas

| Alternativa | Por qué se descarta |
| ----------- | ------------------- |
| Contar cada request del detalle | Infla el contador con recargas y navegación repetida: viola RN-08. |
| Deduplicar por IP | Comparte IP entre usuarios de la misma red (hogares, oficinas): subcuenta visitas reales; además IPs cambian. |
| Solo localStorage del navegador | No llega al servidor: el backend no puede auditar ni recomputar; se pierde con datos de navegación. |
| Fingerprinting agresivo | Complejo, frágil y con problemas de privacidad para un MVP. |

## Consecuencias

- Positivas: métrica estable ante recargas; funciona igual para anónimos y registrados; auditable desde el servidor.
- Negativas: requiere emisión de cookie (aceptable, funcional y no publicitaria); cambiar de dispositivo/navegador puede contar una visita extra (aceptado para MVP).
- Pendiente: definir si la ventana de deduplicación es fija (24 h) o configurable.
