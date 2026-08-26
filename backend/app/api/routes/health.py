"""Health endpoints.

- GET /health  → readiness: app status + database connectivity + config.
- GET /healthz → liveness: process is up, no dependency checks.
"""

from fastapi import APIRouter

from app.core.config import get_settings
from app.db.base import check_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "app": "punto-app-api",
        "database": "up" if check_db() else "down",
        "visit_dedup_window_hours": settings.visit_dedup_window_hours,
    }


@router.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}
