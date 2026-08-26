"""Punto App API entrypoint.

FastAPI REST backend (ADR-004) serving two isolated audiences:
store tokens and admin tokens (ADR-003/ADR-005). Business endpoints
are added per the API design phase.

Startup runs the idempotent admin bootstrap (ADR-006).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.core.bootstrap import run_bootstrap
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # BOOT-01..04: crea el administrador inicial si corresponde.
    run_bootstrap()
    yield


app = FastAPI(
    title="Punto App API",
    version="0.1.0",
    description="Ecommerce ferretería — backend REST (SDD project)",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,  # required: JWT travels in cookies (ADR-003)
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
