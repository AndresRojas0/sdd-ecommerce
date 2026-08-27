"""Cart & Orders — RN-12, RN-23, RN-26, RN-28, RN-29, RN-34."""
from __future__ import annotations

import uuid
from decimal import Decimal

from tests.conftest import auth_client_for, create_product_fixture


def test_cart_server_side_survives(client, categoria, unidad, vendedor, comprador):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    headers = auth_client_for(client, comprador)
    # Add item
    resp = client.post("/carts/me/items", json={"product_id": prod["id"], "cantidad": "2"}, headers=headers)
    assert resp.status_code == 201
    # Get cart
    resp2 = client.get("/carts/me", headers=headers)
    assert resp2.status_code == 200
    assert len(resp2.json()["items"]) == 1
    # Logout and login again (cart survives)
    client.post("/auth/logout", headers=headers)
    headers2 = auth_client_for(client, comprador)
    resp3 = client.get("/carts/me", headers=headers2)
    assert resp3.status_code == 200
    assert len(resp3.json()["items"]) == 1


def test_cart_quantity_update_and_clear(client, categoria, unidad, vendedor, comprador):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    headers = auth_client_for(client, comprador)
    resp = client.post("/carts/me/items", json={"product_id": prod["id"], "cantidad": "1"}, headers=headers)
    item_id = resp.json()["id"]
    # Update
    resp2 = client.put(f"/carts/me/items/{item_id}", json={"cantidad": "3.5"}, headers=headers)
    assert resp2.status_code == 200
    assert str(resp2.json()["cantidad"]) == "3.50" or str(resp2.json()["cantidad"]) == "3.5"
    # Clear
    resp3 = client.delete("/carts/me", headers=headers)
    assert resp3.status_code == 204
    resp4 = client.get("/carts/me", headers=headers)
    assert len(resp4.json()["items"]) == 0


def test_order_create_from_cart(client, categoria, unidad, vendedor, comprador):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    headers = auth_client_for(client, comprador)
    client.delete("/carts/me", headers=headers)
    client.post("/carts/me/items", json={"product_id": prod["id"], "cantidad": "2"}, headers=headers)
    resp = client.post("/orders", headers=headers)
    assert resp.status_code == 201
    assert resp.json()["estado"] == "pendiente"
    assert resp.json()["subtotal"] is not None
    # Cart should be cleared
    resp2 = client.get("/carts/me", headers=headers)
    assert len(resp2.json()["items"]) == 0


def test_order_edit_only_pending_RN28(client, categoria, unidad, vendedor, comprador, admin):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    headers = auth_client_for(client, comprador)
    client.delete("/carts/me", headers=headers)
    client.post("/carts/me/items", json={"product_id": prod["id"], "cantidad": "1"}, headers=headers)
    order = client.post("/orders", headers=headers).json()
    oid = order["id"]
    # Edit pending should succeed
    prod2 = create_product_fixture(client, categoria, unidad, vendedor, slug_suffix=uuid.uuid4().hex[:6])
    resp = client.put(f"/orders/{oid}", json={"items": [{"product_id": prod2["id"], "cantidad": "5"}]}, headers=headers)
    assert resp.status_code == 200
    # Accept order as admin
    headers_admin = auth_client_for(client, admin)
    resp_acc = client.post(f"/admin/orders/{oid}/accept", headers=headers_admin)
    assert resp_acc.status_code == 200
    # Edit after accepted should 409
    resp2 = client.put(f"/orders/{oid}", json={"items": [{"product_id": prod["id"], "cantidad": "1"}]}, headers=headers)
    assert resp2.status_code == 409


def test_order_duplicate_rejected_RN28(client, categoria, unidad, vendedor, comprador, admin):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    headers = auth_client_for(client, comprador)
    client.delete("/carts/me", headers=headers)
    client.post("/carts/me/items", json={"product_id": prod["id"], "cantidad": "1"}, headers=headers)
    order = client.post("/orders", headers=headers).json()
    oid = order["id"]
    headers_admin = auth_client_for(client, admin)
    client.post(f"/admin/orders/{oid}/reject", json={"motivo_rechazo": "sin stock"}, headers=headers_admin)
    # Duplicate
    resp = client.post(f"/orders/{oid}/duplicate", headers=headers)
    assert resp.status_code == 201
    assert resp.json()["estado"] == "pendiente"


def test_order_consolidate_RN29(client, categoria, unidad, vendedor, comprador, admin):
    # Create two orders same comprador
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    headers = auth_client_for(client, comprador)
    for _ in range(2):
        client.delete("/carts/me", headers=headers)
        client.post("/carts/me/items", json={"product_id": prod["id"], "cantidad": "1"}, headers=headers)
        client.post("/orders", headers=headers)
    # List orders to get ids
    orders = client.get("/orders", headers=headers).json()["items"]
    pending_ids = [o["id"] for o in orders if o["estado"] == "pendiente"][-2:]
    assert len(pending_ids) >= 2
    headers_admin = auth_client_for(client, admin)
    resp = client.post("/admin/orders/consolidate", json={"pedido_ids": pending_ids}, headers=headers_admin)
    assert resp.status_code == 200
    assert "orden_compra" in resp.json()
    # Consolidate different buyers should 409
    from app.core.security import hash_password
    from app.models.user import User

    # Create second buyer via register
    resp_reg = client.post(
        "/auth/register", json={"email": f"other{uuid.uuid4().hex[:4]}@test.com", "display_name": "Other", "password": "Abcdef1!"}
    )
    other_email = resp_reg.json()["email"]
    other_headers = auth_client_for(client, type("U", (), {"email": other_email})())
    # Create order for other
    client.delete("/carts/me", headers=other_headers)
    client.post("/carts/me/items", json={"product_id": prod["id"], "cantidad": "1"}, headers=other_headers)
    other_order = client.post("/orders", headers=other_headers).json()
    # Try consolidate mixed
    # Need fresh pending from comprador
    client.delete("/carts/me", headers=headers)
    client.post("/carts/me/items", json={"product_id": prod["id"], "cantidad": "1"}, headers=headers)
    new_order = client.post("/orders", headers=headers).json()
    resp2 = client.post(
        "/admin/orders/consolidate", json={"pedido_ids": [new_order["id"], other_order["id"]]}, headers=headers_admin
    )
    assert resp2.status_code in (409, 422)


def test_order_reassign_RN27(client, categoria, unidad, vendedor, comprador, admin, db_session):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    headers = auth_client_for(client, comprador)
    client.delete("/carts/me", headers=headers)
    client.post("/carts/me/items", json={"product_id": prod["id"], "cantidad": "1"}, headers=headers)
    order = client.post("/orders", headers=headers).json()
    # Create second vendedor
    from app.core.security import hash_password
    from app.models.user import User

    v2 = User(email=f"v2{uuid.uuid4().hex[:4]}@test.com", display_name="V2", password_hash=hash_password("Abcdef1!"), role="vendedor")
    db_session.add(v2)
    db_session.commit()
    db_session.refresh(v2)
    headers_admin = auth_client_for(client, admin)
    resp = client.patch(f"/admin/orders/{order['id']}/reassign", json={"to_vendedor_id": str(v2.id)}, headers=headers_admin)
    assert resp.status_code == 200
    assert resp.json()["vendedor_id"] == str(v2.id)
