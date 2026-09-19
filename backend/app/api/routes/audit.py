"""Audit read endpoint — A-AUD-01 (02-security.md, auditoría de staff).

Lectura append-only de staff_audits: sin POST/PUT/PATCH/DELETE nunca.
Solo rol `administrador`.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin_role
from app.db.base import get_db
from app.models.staff_audit import StaffAudit
from app.models.user import User

router = APIRouter(prefix="/admin/audit", tags=["admin-audit"])


@router.get("", response_model=dict)
def list_audit(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role("administrador")),
    actor_id: uuid.UUID | None = Query(default=None),
    entidad: str | None = Query(default=None),
    from_date: date | None = Query(default=None, alias="from", description="Fecha desde (inclusive)"),
    to_date: date | None = Query(default=None, alias="to", description="Fecha hasta (inclusive)"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """A-AUD-01: consulta de la auditoría de staff (más reciente primero)."""
    filters = []
    if actor_id is not None:
        filters.append(StaffAudit.actor_id == actor_id)
    if entidad:
        filters.append(StaffAudit.entidad == entidad)
    if from_date is not None:
        start = datetime.combine(from_date, time.min, tzinfo=timezone.utc)
        filters.append(StaffAudit.created_at >= start)
    if to_date is not None:
        end = datetime.combine(to_date, time.min, tzinfo=timezone.utc)
        filters.append(StaffAudit.created_at < end + timedelta(days=1))
    base = select(StaffAudit)
    count_base = select(func.count()).select_from(StaffAudit)
    if filters:
        from sqlalchemy import and_

        base = base.where(and_(*filters))
        count_base = count_base.where(and_(*filters))
    total = db.scalar(count_base) or 0
    rows = db.scalars(base.order_by(StaffAudit.created_at.desc()).limit(limit).offset(offset)).all()
    items = [
        {
            "id": str(r.id),
            "actor_id": str(r.actor_id) if r.actor_id else None,
            "accion": r.accion,
            "entidad": r.entidad,
            "entidad_id": r.entidad_id,
            "datos_antes": r.datos_antes,
            "datos_despues": r.datos_despues,
            "request_id": r.request_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return {"total": total, "limit": limit, "offset": offset, "items": items}
