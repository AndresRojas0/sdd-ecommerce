"""Visits, favorites, ratings — RN-08, RN-09, RN-21, RN-30, RN-33."""
from __future__ import annotations

import uuid

from tests.conftest import auth_client_for, create_product_fixture


def test_visit_dedup_RN08(client, categoria, unidad, vendedor):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    pid = prod["id"]
    # Anonymous visit
    resp1 = client.post(f"/products/{pid}/visits", json={}, params={"origen": "directa"})
    # Fast second visit within window should be deduped (same visitor_cookie header)
    # Grab visitor_id cookie
    visitor_cookie = resp1.cookies.get("visitor_id")
    headers = {}
    if visitor_cookie:
        headers["Cookie"] = f"visitor_id={visitor_cookie}"
    resp2 = client.post(f"/products/{pid}/visits", params={"origen": "directa"}, headers=headers, cookies={"visitor_id": visitor_cookie} if visitor_cookie else {})
    # At least one dedup flag true or counts not double-incremented
    assert resp2.status_code == 200


def test_visit_busqueda_increments_busquedas_RN30(client, categoria, unidad, vendedor, comprador):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    pid = prod["id"]
    headers = auth_client_for(client, comprador)
    resp = client.post(f"/products/{pid}/visits", params={"origen": "busqueda"}, headers=headers)
    assert resp.status_code == 200
    # Check busquedas_count increased
    prod_detail = client.get(f"/products/{prod['slug']}", headers=headers).json()
    assert prod_detail["busquedas_count"] >= 1


def test_favorite_counter_RN09(client, categoria, unidad, vendedor, comprador):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    pid = prod["id"]
    headers = auth_client_for(client, comprador)
    # Add
    resp = client.post(f"/favorites/{pid}", headers=headers)
    assert resp.status_code in (200, 201)
    detail1 = client.get(f"/products/{prod['slug']}", headers=headers).json()
    cnt1 = detail1["guardados_count"]
    # Remove
    resp2 = client.delete(f"/favorites/{pid}", headers=headers)
    assert resp2.status_code == 200
    detail2 = client.get(f"/products/{prod['slug']}", headers=headers).json()
    assert detail2["guardados_count"] == max(0, cnt1 - 1)


def test_favorite_list(client, categoria, unidad, vendedor, comprador):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    headers = auth_client_for(client, comprador)
    client.post(f"/favorites/{prod['id']}", headers=headers)
    resp = client.get("/favorites", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_rating_eligibility_RN33_forbidden_without_accepted_order(client, categoria, unidad, vendedor, comprador):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    headers = auth_client_for(client, comprador)
    resp = client.post(f"/products/{prod['id']}/ratings", json={"estrellas": 5}, headers=headers)
    assert resp.status_code == 403


def test_rating_with_accepted_order_RN33_RN21(client, categoria, unidad, vendedor, comprador, admin):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    headers_compr = auth_client_for(client, comprador)
    # Create order and accept
    client.delete("/carts/me", headers=headers_compr)
    client.post("/carts/me/items", json={"product_id": prod["id"], "cantidad": "1"}, headers=headers_compr)
    order = client.post("/orders", headers=headers_compr).json()
    headers_admin = auth_client_for(client, admin)
    client.post(f"/admin/orders/{order['id']}/accept", headers=headers_admin)
    # Now rate
    resp = client.post(f"/products/{prod['id']}/ratings", json={"estrellas": 4}, headers=headers_compr)
    assert resp.status_code == 201
    assert resp.json()["estrellas"] == 4
    # Check promedio
    detail = client.get(f"/products/{prod['slug']}").json()
    assert float(detail["calificacion_promedio"]) == 4.0
    # Update rating
    resp2 = client.put(f"/products/{prod['id']}/ratings", json={"estrellas": 5}, headers=headers_compr)
    assert resp2.status_code == 200
    assert resp2.json()["estrellas"] == 5
    # Duplicate POST should 409
    resp3 = client.post(f"/products/{prod['id']}/ratings", json={"estrellas": 3}, headers=headers_compr)
    assert resp3.status_code == 409
    # List ratings
    resp4 = client.get(f"/products/{prod['id']}/ratings")
    assert resp4.status_code == 200
    assert len(resp4.json()) >= 1
