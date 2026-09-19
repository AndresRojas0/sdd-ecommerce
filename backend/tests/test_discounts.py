"""Discounts per ADR-008 — offers, vigencia, con_descuento sorting, price snapshots."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.models.pedido_item import PedidoItem
from tests.conftest import admin_auth_header, auth_client_for, create_product_fixture


def _dec(value) -> Decimal:
    return Decimal(str(value))


def _set_offer(client, vendedor, product_id: str, precio_descuento: str, desde=None, hasta=None):
    body = {"precio_descuento": precio_descuento}
    if desde is not None:
        body["descuento_desde"] = desde.isoformat()
    if hasta is not None:
        body["descuento_hasta"] = hasta.isoformat()
    return client.put(
        f"/products/{product_id}/discount",
        json=body,
        headers=admin_auth_header(client, vendedor.email),
    )


def _store_detail(client, slug: str) -> dict:
    return client.get(f"/products/{slug}").json()


# ---------------------------------------------------------------------------
# Offer management (admin audience) + store payloads
# ---------------------------------------------------------------------------


def test_set_discount_and_store_payloads(client, categoria, unidad, vendedor):
    prod = create_product_fixture(client, categoria, unidad, vendedor)  # precio 10.50
    resp = _set_offer(client, vendedor, prod["id"], "8.40")
    assert resp.status_code == 200, resp.text
    admin_view = resp.json()
    assert _dec(admin_view["precio_descuento"]) == Decimal("8.40")
    assert admin_view["en_descuento"] is True
    assert _dec(admin_view["precio_efectivo"]) == Decimal("8.40")
    assert _dec(admin_view["descuento_porcentaje"]) == Decimal("20.00")

    # Store list (anonymous): pricing fields present, admin fields absent/None
    marker = prod["titulo"]  # unique per fixture; q matches titulo
    listing = client.get("/products", params={"q": marker}).json()
    item = next(i for i in listing["items"] if i["slug"] == prod["slug"])
    assert _dec(item["precio_efectivo"]) == Decimal("8.40")
    assert item["en_descuento"] is True
    assert _dec(item["descuento_porcentaje"]) == Decimal("20.00")
    assert item["precio_descuento"] is None
    assert item["descuento_desde"] is None
    assert item["descuento_hasta"] is None

    # Store detail (anonymous) — same contract
    detail = _store_detail(client, prod["slug"])
    assert _dec(detail["precio_efectivo"]) == Decimal("8.40")
    assert detail["en_descuento"] is True
    assert _dec(detail["descuento_porcentaje"]) == Decimal("20.00")

    # Staff viewing store surface sees admin discount fields too
    staff_headers = auth_client_for(client, vendedor)
    detail_staff = client.get(f"/products/{prod['slug']}", headers=staff_headers).json()
    assert _dec(detail_staff["precio_descuento"]) == Decimal("8.40")


def test_discount_validations_422(client, categoria, unidad, vendedor):
    prod = create_product_fixture(client, categoria, unidad, vendedor)  # precio 10.50
    now = datetime.now(timezone.utc)
    # zero / negative -> 422 (schema validator)
    assert _set_offer(client, vendedor, prod["id"], "0").status_code == 422
    assert _set_offer(client, vendedor, prod["id"], "-1.00").status_code == 422
    # >= precio -> 422
    assert _set_offer(client, vendedor, prod["id"], "10.50").status_code == 422
    assert _set_offer(client, vendedor, prod["id"], "12.00").status_code == 422
    # desde >= hasta -> 422
    resp = _set_offer(client, vendedor, prod["id"], "8.40", desde=now + timedelta(hours=2), hasta=now + timedelta(hours=1))
    assert resp.status_code == 422, resp.text
    # equal timestamps also invalid
    resp = _set_offer(client, vendedor, prod["id"], "8.40", desde=now + timedelta(hours=1), hasta=now + timedelta(hours=1))
    assert resp.status_code == 422
    # unknown product -> 404
    resp = _set_offer(client, vendedor, str(uuid.uuid4()), "8.40")
    assert resp.status_code == 404


def test_delete_discount_clears_offer(client, categoria, unidad, vendedor):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    assert _set_offer(client, vendedor, prod["id"], "8.40").status_code == 200
    headers = admin_auth_header(client, vendedor.email)
    resp = client.delete(f"/products/{prod['id']}/discount", headers=headers)
    assert resp.status_code == 204
    detail = _store_detail(client, prod["slug"])
    assert detail["en_descuento"] is False
    assert _dec(detail["precio_efectivo"]) == Decimal("10.50")
    assert _dec(detail["descuento_porcentaje"]) == Decimal("0.00")
    # Second delete without offer -> 404
    resp2 = client.delete(f"/products/{prod['id']}/discount", headers=headers)
    assert resp2.status_code == 404


def test_discount_endpoints_reject_store_audience(client, categoria, unidad, vendedor, comprador):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    headers_store = auth_client_for(client, comprador)
    resp_put = client.put(
        f"/products/{prod['id']}/discount",
        json={"precio_descuento": "8.40"},
        headers=headers_store,
    )
    assert resp_put.status_code == 401, resp_put.text
    resp_del = client.delete(f"/products/{prod['id']}/discount", headers=headers_store)
    assert resp_del.status_code == 401


# ---------------------------------------------------------------------------
# Vigencia (active window)
# ---------------------------------------------------------------------------


def test_discount_vigencia(client, categoria, unidad, vendedor):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    now = datetime.now(timezone.utc)

    # Future desde -> not active now
    resp = _set_offer(client, vendedor, prod["id"], "8.40", desde=now + timedelta(hours=1))
    assert resp.status_code == 200
    detail = _store_detail(client, prod["slug"])
    assert detail["en_descuento"] is False
    assert _dec(detail["precio_efectivo"]) == Decimal("10.50")
    assert _dec(detail["descuento_porcentaje"]) == Decimal("0.00")

    # Past hasta -> not active now
    resp = _set_offer(client, vendedor, prod["id"], "8.40", hasta=now - timedelta(hours=1))
    assert resp.status_code == 200
    detail = _store_detail(client, prod["slug"])
    assert detail["en_descuento"] is False
    assert _dec(detail["precio_efectivo"]) == Decimal("10.50")

    # Window containing now -> active
    resp = _set_offer(
        client,
        vendedor,
        prod["id"],
        "8.40",
        desde=now - timedelta(hours=1),
        hasta=now + timedelta(hours=1),
    )
    assert resp.status_code == 200
    detail = _store_detail(client, prod["slug"])
    assert detail["en_descuento"] is True
    assert _dec(detail["precio_efectivo"]) == Decimal("8.40")

    # Only-since (no hasta) containing now -> active
    resp = _set_offer(client, vendedor, prod["id"], "9.00", desde=now - timedelta(minutes=5))
    assert resp.status_code == 200
    detail = _store_detail(client, prod["slug"])
    assert detail["en_descuento"] is True
    assert _dec(detail["precio_efectivo"]) == Decimal("9.00")


# ---------------------------------------------------------------------------
# Sorting: orden=con_descuento (RN-07 + ADR-008)
# ---------------------------------------------------------------------------


def test_sort_con_descuento(client, categoria, unidad, vendedor):
    marker = uuid.uuid4().hex[:8]
    p_a = create_product_fixture(client, categoria, unidad, vendedor, slug_suffix=f"{marker}a")  # 10.50
    p_b = create_product_fixture(client, categoria, unidad, vendedor, slug_suffix=f"{marker}b")
    p_c = create_product_fixture(client, categoria, unidad, vendedor, slug_suffix=f"{marker}c")
    # Raise p_b price to 20.00 so percentages differ (50% vs 20%)
    headers = admin_auth_header(client, vendedor.email)
    resp = client.put(f"/products/{p_b['id']}", json={"precio": "20.00"}, headers=headers)
    assert resp.status_code == 200
    assert _set_offer(client, vendedor, p_a["id"], "8.40").status_code == 200  # 20%
    assert _set_offer(client, vendedor, p_b["id"], "10.00").status_code == 200  # 50%
    # p_c without offer

    listing = client.get("/products", params={"q": marker, "sort": "con_descuento"}).json()
    slugs = [i["slug"] for i in listing["items"]]
    # Only actively-offered products, higher % first
    assert slugs == [p_b["slug"], p_a["slug"]]
    assert listing["total"] == 2


# ---------------------------------------------------------------------------
# Price snapshots (cart, order create, order edit)
# ---------------------------------------------------------------------------


def test_price_snapshots_cart_and_orders(client, categoria, unidad, vendedor, comprador, db_session):
    prod = create_product_fixture(client, categoria, unidad, vendedor)  # precio 10.50
    assert _set_offer(client, vendedor, prod["id"], "8.40").status_code == 200

    headers = auth_client_for(client, comprador)
    client.delete("/carts/me", headers=headers)
    resp = client.post("/carts/me/items", json={"product_id": prod["id"], "cantidad": "2"}, headers=headers)
    assert resp.status_code == 201
    assert _dec(resp.json()["precio_unitario"]) == Decimal("8.40")
    assert _dec(resp.json()["subtotal"]) == Decimal("16.80")

    # Merge on existing item re-snapshots too
    resp = client.post("/carts/me/items", json={"product_id": prod["id"], "cantidad": "3"}, headers=headers)
    assert resp.status_code == 201
    assert _dec(resp.json()["cantidad"]) == Decimal("3.00") or _dec(resp.json()["cantidad"]) == Decimal("3")
    assert _dec(resp.json()["precio_unitario"]) == Decimal("8.40")

    # Order creation IGNORES cart stored prices: fresh snapshot
    resp = client.post("/orders", headers=headers)
    assert resp.status_code == 201, resp.text
    order = resp.json()
    assert _dec(order["total"]) == Decimal("25.20")  # 3 x 8.40
    item = order["items"][0]
    assert _dec(item["precio_unitario"]) == Decimal("8.40")
    assert _dec(item["precio_lista"]) == Decimal("10.50")
    assert _dec(item["subtotal"]) == Decimal("25.20")

    # DB rows: precio_unitario = efectivo, precio_lista = lista
    rows = db_session.scalars(select(PedidoItem).where(PedidoItem.pedido_id == uuid.UUID(order["id"]))).all()
    assert len(rows) == 1
    assert rows[0].precio_unitario == Decimal("8.40")
    assert rows[0].precio_lista == Decimal("10.50")

    # Change the offer, then edit the pendiente order -> lines re-snapshot
    assert _set_offer(client, vendedor, prod["id"], "5.25").status_code == 200  # 50%
    resp = client.put(f"/orders/{order['id']}", json={"items": [{"product_id": prod["id"], "cantidad": "2"}]}, headers=headers)
    assert resp.status_code == 200, resp.text
    edited = resp.json()
    assert _dec(edited["total"]) == Decimal("10.50")
    item = edited["items"][0]
    assert _dec(item["precio_unitario"]) == Decimal("5.25")
    assert _dec(item["precio_lista"]) == Decimal("10.50")
    assert _dec(item["subtotal"]) == Decimal("10.50")

    rows = db_session.scalars(select(PedidoItem).where(PedidoItem.pedido_id == uuid.UUID(order["id"]))).all()
    assert rows[0].precio_unitario == Decimal("5.25")
    assert rows[0].precio_lista == Decimal("10.50")


def test_cart_quantity_update_re_snapshots_effective_price(client, categoria, unidad, vendedor, comprador):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    headers = auth_client_for(client, comprador)
    client.delete("/carts/me", headers=headers)
    resp = client.post("/carts/me/items", json={"product_id": prod["id"], "cantidad": "1"}, headers=headers)
    item_id = resp.json()["id"]
    assert _dec(resp.json()["precio_unitario"]) == Decimal("10.50")  # sin oferta aún

    assert _set_offer(client, vendedor, prod["id"], "8.40").status_code == 200
    resp = client.put(f"/carts/me/items/{item_id}", json={"cantidad": "2"}, headers=headers)
    assert resp.status_code == 200
    assert _dec(resp.json()["precio_unitario"]) == Decimal("8.40")
    assert _dec(resp.json()["subtotal"]) == Decimal("16.80")
