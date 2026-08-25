"""Punto App API entrypoint.

FastAPI REST backend (ADR-004) serving two isolated audiences:
store tokens and admin tokens (ADR-003/ADR-005). Business endpoints
are added per the API design phase; this skeleton only boots the app.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Punto App API",
    version="0.1.0",
    description="Ecommerce ferretería — backend REST (SDD project)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,  # required: JWT travels in cookies (ADR-003)
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
