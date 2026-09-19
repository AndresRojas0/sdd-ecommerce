"""Audit helper — escritura append-only en staff_audits (02-security.md, A-AUD-01).

Solo INSERT: nunca UPDATE ni DELETE. La fila se agrega en la MISMA
transacción de la operación auditada, de modo que solo persiste si la
operación tuvo éxito (commit atómico).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.staff_audit import StaffAudit
from app.models.user import User


def _json_safe(value: Any) -> Any:
    """Convierte valores no serializables a JSON (UUID, Decimal, fecha, etc.)."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (uuid.UUID,)):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return str(value)


def registrar_auditoria(
    db: Session,
    request: Request | None,
    actor: User | None,
    accion: str,
    entidad: str,
    entidad_id: uuid.UUID | str | None = None,
    antes: dict | None = None,
    despues: dict | None = None,
) -> None:
    """Inserta una fila de auditoría (append-only) en la transacción actual.

    - `actor`: usuario staff que ejecuta la operación (None si sistema).
    - `antes`/`despues`: estado relevante antes/después (JSON-safe).
    - `request_id`: del header `x-request-id` si está presente.
    """
    row = StaffAudit(
        actor_id=actor.id if actor is not None else None,
        accion=accion,
        entidad=entidad,
        entidad_id=str(entidad_id) if entidad_id is not None else None,
        datos_antes=_json_safe(antes or {}),
        datos_despues=_json_safe(despues or {}),
        request_id=(request.headers.get("x-request-id") if request is not None else None),
    )
    # Truncar request_id al límite de la columna (defensivo).
    if row.request_id is not None and len(row.request_id) > 64:
        row.request_id = row.request_id[:64]
    db.add(row)
    db.flush()
