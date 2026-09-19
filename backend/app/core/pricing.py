"""Pricing helpers — ADR-008 discounts.

Single source of truth for effective price / active-offer logic shared by
products payloads, cart snapshots and order snapshots.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from app.models.producto import Producto


def _as_aware(dt: datetime) -> datetime:
    """SQLite returns naive datetimes; treat stored wall time as UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _utcnow(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(timezone.utc)
    return _as_aware(now)


def descuento_activo(producto: Producto, now: datetime | None = None) -> bool:
    """La oferta está activa si hay precio_descuento y `now` cae en la vigencia.

    Vigencia abierta: desde/hasta son independientes; None = sin límite.
    """
    if producto.precio_descuento is None:
        return False
    at = _utcnow(now)
    if producto.descuento_desde is not None and at < _as_aware(producto.descuento_desde):
        return False
    if producto.descuento_hasta is not None and at > _as_aware(producto.descuento_hasta):
        return False
    return True


def precio_efectivo(producto: Producto, now: datetime | None = None) -> Decimal:
    """Precio con oferta aplicada si está vigente; si no, precio de lista."""
    if descuento_activo(producto, now):
        return producto.precio_descuento  # type: ignore[return-value]
    return producto.precio


def descuento_porcentaje(producto: Producto, now: datetime | None = None) -> Decimal:
    """Porcentaje de descuento vigente (2 decimales); 0.00 si no hay oferta activa."""
    if not descuento_activo(producto, now):
        return Decimal("0.00")
    precio = producto.precio
    if precio is None or precio <= 0:
        return Decimal("0.00")
    pct = (precio - producto.precio_descuento) * Decimal("100") / precio
    return pct.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
