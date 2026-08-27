"""Visits — RN-08 dedup, RN-30 relevance, ADR-001."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_optional_user
from app.core.config import get_settings
from app.db.base import get_db
from app.models.producto import Producto
from app.models.user import User
from app.models.visita import Visita

router = APIRouter(prefix="/products", tags=["visits"])


@router.post("/{product_id}/visits")
def create_visit(
    product_id: uuid.UUID,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    origen: str = "directa",
    current_user: User | None = Depends(get_optional_user),
    visitor_id: str | None = Cookie(default=None),
    x_visitor_id: str | None = Header(default=None, alias="X-Visitor-Id"),
):
    if origen not in ("directa", "busqueda"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="origen debe ser directa o busqueda")
    prod = db.get(Producto, product_id)
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    # Resolve visitor identity
    user_id = current_user.id if current_user else None
    visitor_cookie = None
    if not user_id:
        visitor_cookie = x_visitor_id or visitor_id
        if not visitor_cookie:
            visitor_cookie = str(uuid.uuid4())
            # Set cookie for future dedup (Secure False for dev)
            response.set_cookie(
                key="visitor_id",
                value=visitor_cookie,
                httponly=False,
                secure=False,
                samesite="lax",
                path="/",
                max_age=365 * 24 * 3600,
            )
        else:
            # Ensure cookie is set if came via header
            if not visitor_id:
                response.set_cookie(
                    key="visitor_id",
                    value=visitor_cookie,
                    httponly=False,
                    secure=False,
                    samesite="lax",
                    path="/",
                    max_age=365 * 24 * 3600,
                )

    settings = get_settings()
    window = timedelta(hours=settings.visit_dedup_window_hours)
    cutoff = datetime.now(timezone.utc) - window

    # Dedup check
    if user_id:
        exists = db.scalar(
            select(Visita).where(
                Visita.product_id == product_id,
                Visita.user_id == user_id,
                Visita.visited_at > cutoff,
            )
        )
    else:
        exists = db.scalar(
            select(Visita).where(
                Visita.product_id == product_id,
                Visita.visitor_cookie == visitor_cookie,
                Visita.visited_at > cutoff,
            )
        )
    if exists:
        return {"deduped": True, "visitas_count": prod.visitas_count, "busquedas_count": prod.busquedas_count}

    visita = Visita(
        product_id=product_id,
        user_id=user_id,
        visitor_cookie=visitor_cookie if not user_id else None,
        origen=origen,
        visited_at=datetime.now(timezone.utc),
    )
    db.add(visita)
    prod.visitas_count = (prod.visitas_count or 0) + 1
    if origen == "busqueda":
        prod.busquedas_count = (prod.busquedas_count or 0) + 1
    db.commit()
    db.refresh(prod)
    return {"deduped": False, "visitas_count": prod.visitas_count, "busquedas_count": prod.busquedas_count}
