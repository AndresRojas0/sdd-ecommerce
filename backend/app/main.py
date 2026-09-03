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

from app.api.routes.admin_users import router as admin_users_router
from app.api.routes.auth import router as auth_router
from app.api.routes.carts import router as carts_router
from app.api.routes.categorias import router as categorias_router
from app.api.routes.colecciones import router as colecciones_router
from app.api.routes.etiquetas import router as etiquetas_router
from app.api.routes.favorites import router as favorites_router
from app.api.routes.health import router as health_router
from app.api.routes.orders import admin_router as admin_orders_router
from app.api.routes.orders import dashboard_router as dashboard_router
from app.api.routes.orders import purchase_router as purchase_orders_router
from app.api.routes.orders import router as orders_router
from app.api.routes.orders import stock_router as stock_router
from app.api.routes.products import router as products_router
from app.api.routes.ratings import router as ratings_router
from app.api.routes.unidades import router as unidades_router
from app.api.routes.users import router as users_router
from app.api.routes.visits import router as visits_router
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
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_users_router)
app.include_router(categorias_router)
app.include_router(colecciones_router)
app.include_router(etiquetas_router)
app.include_router(unidades_router)
app.include_router(products_router)
app.include_router(visits_router)
app.include_router(favorites_router)
app.include_router(ratings_router)
app.include_router(carts_router)
app.include_router(orders_router)
app.include_router(admin_orders_router)
app.include_router(purchase_orders_router)
app.include_router(stock_router)
app.include_router(dashboard_router)
