# Definition of done

Checklist de terminado para toda tarea o cambio. Un ítem declarado "done"
que no cumple esto no está done.

- [ ] 1. Tests en verde: `PYTHONPATH=backend pytest -q`. Toda `RN` afectada
      tiene TCs nuevos o actualizados.
- [ ] 2. Endpoints nuevos o modificados registrados con su ID en
      `docs/architecture/01-api-design.md` y bindeados en
      `docs/testing/01-test-cases.md`.
- [ ] 3. Si el esquema cambió: migración Alembic incluida (forward-only) y
      `docs/domain/data-model.md` actualizado.
- [ ] 4. Docs afectadas actualizadas, sin stubs "pendiente" nuevos.
- [ ] 5. Commits convencionales, sin atribución de IA, en unidades de
      trabajo coherentes (tests y docs junto al código).
- [ ] 6. Sin secrets ni valores de entorno commiteados.
- [ ] 7. Si tocó reglas de negocio: la `RN` está citada en la spec y el
      código coincide con lo que la RN dice.

Aplica a cualquier tarea: código, docs, migraciones o infra. Ante la duda,
el checklist manda sobre la estimación o el plazo.
