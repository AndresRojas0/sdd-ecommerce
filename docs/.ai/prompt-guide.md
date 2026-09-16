# Guía de prompts — cómo pedir cambios en este repo

1. **Referenciá IDs.** Cada pedido cita los identificadores involucrados:
   - Requisitos: `RF-xx`, `RN-xx`, `UC-xx`.
   - Endpoints: `S-*` (store) y `A-*` (admin), según
     `docs/architecture/01-api-design.md`.
   - Pruebas: `TC-xx`, según `docs/testing/01-test-cases.md`.

2. **Un cambio lógico por vez.** Un pedido que mezcla features distintas
   se parte antes de implementar.

3. **Docs primero.** Toda feature nueva se especifica antes que el código
   (ver `workflow.md`).

4. **Reglas de negocio con respaldo.** Si el cambio toca una regla de
   negocio, la petición cita la `RN` que la respalda. Si ninguna la cubre,
   eso es una pregunta abierta, no una decisión implícita.

5. **Decisiones ya tomadas: citar el ADR.** Los ADRs (`001`..`008`) se
   revisan y se discuten; no se bypasean. Si tu pedido contradice un ADR,
   explicitalo para abrir su revisión.

6. **Idiomas.** La documentación se escribe en español neutro. El código y
   sus identificadores van en inglés.
