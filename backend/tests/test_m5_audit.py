"""M5 — remaining admin endpoints + staff audit table (A-USR-03/05/06, A-COL-06,
A-PED-06, A-STK-03, A-FAC-01/02, A-AUD-01; TC-RN27-02, TC-AUD-01, TC-M5-01)."""
from __future__ import annotations

import uuid
from decimal import Decimal

from tests.conftest import admin_auth_header, auth_client_for, create_product_fixture


def _admin_headers(client, admin) -> dict:
    return admin_auth_header(client, admin.email)


def _create_order(client, comprador, prod, cantidad="2") -> dict:
    headers = auth_client_for(client, comprador)
    client.delete("/carts/me", headers=headers)
    resp = client.post("/carts/me/items", json={"product_id": prod["id"], "cantidad": cantidad}, headers=headers)
    assert resp.status_code == 201, resp.text
    resp2 = client.post("/orders", headers=headers)
    assert resp2.status_code == 201, resp2.text
    return resp2.json()


def _audit_rows(client, admin, **params) -> list[dict]:
    resp = client.get("/admin/audit", params=params, headers=_admin_headers(client, admin))
    assert resp.status_code == 200, resp.text
    return resp.json()["items"]


# ---------------------------------------------------------------------------
# A-USR-03 — PATCH /admin/users/{user_id}
# ---------------------------------------------------------------------------


def test_patch_profile_ok_and_rejects_role_password(client, admin, comprador):
    headers = _admin_headers(client, admin)
    # Edición acotada permitida
    resp = client.patch(f"/admin/users/{comprador.id}", json={"display_name": "Nombre Editado"}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["display_name"] == "Nombre Editado"
    # rol y contraseña NUNCA editables por esta vía (422)
    resp2 = client.patch(f"/admin/users/{comprador.id}", json={"role": "administrador"}, headers=headers)
    assert resp2.status_code == 422
    resp3 = client.patch(f"/admin/users/{comprador.id}", json={"password": "NuevaClave1!"}, headers=headers)
    assert resp3.status_code == 422
    # La fila de auditoría existe
    rows = _audit_rows(client, admin, entidad="usuario")
    match = [r for r in rows if r["accion"] == "usuario.editar_perfil" and r["entidad_id"] == str(comprador.id)]
    assert match, "falta auditoría usuario.editar_perfil"
    assert match[0]["datos_despues"]["display_name"] == "Nombre Editado"


# ---------------------------------------------------------------------------
# A-USR-05 / A-USR-06 — métricas y pedidos del usuario
# ---------------------------------------------------------------------------


def test_user_metrics_and_orders(client, admin, comprador, categoria, unidad, vendedor):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    order = _create_order(client, comprador, prod, cantidad="2")
    headers = _admin_headers(client, admin)

    resp = client.get(f"/admin/users/{comprador.id}/metrics", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["orders_count"] == 1
    assert Decimal(data["total_spent"]) == Decimal(order["total"])
    assert data["last_order_at"] is not None

    resp2 = client.get(f"/admin/users/{comprador.id}/orders", headers=headers)
    assert resp2.status_code == 200, resp2.text
    listing = resp2.json()
    assert listing["total"] == 1
    assert listing["items"][0]["id"] == order["id"]
    assert listing["items"][0]["estado"] == "pendiente"

    # Usuario inexistente → 404
    resp3 = client.get(f"/admin/users/{uuid.uuid4()}/metrics", headers=headers)
    assert resp3.status_code == 404
    resp4 = client.get(f"/admin/users/{uuid.uuid4()}/orders", headers=headers)
    assert resp4.status_code == 404


# ---------------------------------------------------------------------------
# A-COL-06 — PATCH /colecciones/{id}/destacada
# ---------------------------------------------------------------------------


def test_coleccion_destacada_toggle_and_audit(client, admin):
    headers = _admin_headers(client, admin)
    resp = client.post(
        "/colecciones",
        json={"nombre": "Ofertas M5", "slug": f"ofertas-m5-{uuid.uuid4().hex[:6]}", "destacada": False},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    col_id = resp.json()["id"]

    resp2 = client.patch(f"/colecciones/{col_id}/destacada", json={"destacada": True}, headers=headers)
    assert resp2.status_code == 200, resp2.text
    assert resp2.json()["destacada"] is True

    resp3 = client.patch(f"/colecciones/{col_id}/destacada", json={"destacada": False}, headers=headers)
    assert resp3.status_code == 200, resp3.text
    assert resp3.json()["destacada"] is False

    rows = _audit_rows(client, admin, entidad="coleccion")
    toggles = [r for r in rows if r["accion"] == "coleccion.destacada" and r["entidad_id"] == col_id]
    assert len(toggles) >= 2
    # rows vienen más-nuevo-primero: [0] = segundo toggle (True→False), [1] = primero (False→True)
    assert toggles[1]["datos_antes"]["destacada"] is False and toggles[1]["datos_despues"]["destacada"] is True
    assert toggles[0]["datos_antes"]["destacada"] is True and toggles[0]["datos_despues"]["destacada"] is False


# ---------------------------------------------------------------------------
# A-PED-06 — PATCH /admin/orders/{pedido_id}/lines
# ---------------------------------------------------------------------------


def test_lines_edit_resnaps_prices_recomputes_total_and_409_on_accepted(client, admin, comprador, categoria, unidad, vendedor):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    vendedor_headers = admin_auth_header(client, vendedor.email)
    admin_headers = _admin_headers(client, admin)

    # Pedido creado en nombre del cliente (vendedor) a precio de lista 10.50
    resp = client.post(
        "/admin/orders",
        json={"user_id": str(comprador.id), "items": [{"product_id": prod["id"], "cantidad": "2"}]},
        headers=vendedor_headers,
    )
    assert resp.status_code == 201, resp.text
    pedido = resp.json()
    assert Decimal(pedido["total"]) == Decimal("21.00")
    line_id = pedido["items"][0]["id"]

    # Oferta activa DESPUÉS del snapshot: el re-snapshot debe tomar 8.00 (ADR-008)
    resp_disc = client.put(f"/products/{prod['id']}/discount", json={"precio_descuento": "8.00"}, headers=vendedor_headers)
    assert resp_disc.status_code == 200, resp_disc.text

    resp2 = client.patch(
        f"/admin/orders/{pedido['id']}/lines",
        json={"updates": [{"line_id": line_id, "cantidad": "3"}]},
        headers=vendedor_headers,
    )
    assert resp2.status_code == 200, resp2.text
    edited = resp2.json()
    assert Decimal(edited["items"][0]["precio_unitario"]) == Decimal("8.00")
    assert Decimal(edited["items"][0]["precio_lista"]) == Decimal("10.50")
    assert Decimal(edited["items"][0]["subtotal"]) == Decimal("24.00")
    assert Decimal(edited["total"]) == Decimal("24.00")

    # Aceptado → ya no es editable (RN-28) → 409
    resp_acc = client.post(f"/admin/orders/{pedido['id']}/accept", headers=vendedor_headers)
    assert resp_acc.status_code == 200, resp_acc.text
    resp3 = client.patch(
        f"/admin/orders/{pedido['id']}/lines",
        json={"updates": [{"line_id": line_id, "cantidad": "1"}]},
        headers=vendedor_headers,
    )
    assert resp3.status_code == 409

    # Auditoría con antes/después de líneas
    rows = _audit_rows(client, admin, entidad="pedido")
    edits = [r for r in rows if r["accion"] == "pedido.editar_lineas" and r["entidad_id"] == pedido["id"]]
    assert edits, "falta auditoría pedido.editar_lineas"
    antes = edits[0]["datos_antes"]
    despues = edits[0]["datos_despues"]
    assert len(antes["lineas"]) == 1 and len(despues["lineas"]) == 1
    assert Decimal(str(antes["lineas"][0]["cantidad"])) == Decimal("2.00")
    assert Decimal(str(despues["lineas"][0]["cantidad"])) == Decimal("3.00")
    assert Decimal(str(antes["total"])) == Decimal("21.00")
    assert Decimal(str(despues["total"])) == Decimal("24.00")


def test_lines_edit_add_and_remove(client, admin, comprador, categoria, unidad, vendedor):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    prod2 = create_product_fixture(client, categoria, unidad, vendedor, slug_suffix=uuid.uuid4().hex[:6])
    vendedor_headers = admin_auth_header(client, vendedor.email)
    order = _create_order(client, comprador, prod, cantidad="1")

    # Agregar línea
    resp = client.patch(
        f"/admin/orders/{order['id']}/lines",
        json={"add": [{"product_id": prod2["id"], "cantidad": "2"}]},
        headers=vendedor_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["items"]) == 2
    assert Decimal(body["total"]) == Decimal("31.50")
    new_line = next(i for i in body["items"] if i["product_id"] == prod2["id"])

    # Quitar línea original
    resp2 = client.patch(
        f"/admin/orders/{order['id']}/lines",
        json={"remove": [order["items"][0]["id"]]},
        headers=vendedor_headers,
    )
    assert resp2.status_code == 200, resp2.text
    body2 = resp2.json()
    assert len(body2["items"]) == 1
    assert Decimal(body2["total"]) == Decimal("21.00")

    # No puede quedar vacío
    resp3 = client.patch(
        f"/admin/orders/{order['id']}/lines",
        json={"remove": [new_line["id"]]},
        headers=vendedor_headers,
    )
    assert resp3.status_code == 422

    # Línea inexistente → 422
    resp4 = client.patch(
        f"/admin/orders/{order['id']}/lines",
        json={"remove": [str(uuid.uuid4())]},
        headers=vendedor_headers,
    )
    assert resp4.status_code == 422


# ---------------------------------------------------------------------------
# A-STK-03 — GET /admin/stock/movements
# ---------------------------------------------------------------------------


def test_stock_movements_list_from_accept_and_reject(client, admin, comprador, categoria, unidad, vendedor):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    vendedor_headers = admin_auth_header(client, vendedor.email)
    order = _create_order(client, comprador, prod, cantidad="2")

    resp = client.post(f"/admin/orders/{order['id']}/accept", headers=vendedor_headers)
    assert resp.status_code == 200, resp.text

    resp2 = client.get("/admin/stock/movements", headers=_admin_headers(client, admin))
    assert resp2.status_code == 200, resp2.text
    data = resp2.json()
    assert data["total"] >= 1
    reservas = [m for m in data["items"] if m["tipo"] == "reserva" and m["pedido_id"] == order["id"]]
    assert reservas, "no hay movimiento reserva del pedido"
    assert reservas[0]["product_id"] == prod["id"]

    # Filtro por product_id
    resp3 = client.get(f"/admin/stock/movements?product_id={prod['id']}", headers=_admin_headers(client, admin))
    assert resp3.status_code == 200
    assert all(m["product_id"] == prod["id"] for m in resp3.json()["items"])

    # Rechazo desde aceptado genera devolución
    resp_rej = client.post(
        f"/admin/orders/{order['id']}/reject",
        json={"motivo_rechazo": "cliente canceló"},
        headers=vendedor_headers,
    )
    assert resp_rej.status_code == 200, resp_rej.text
    resp4 = client.get("/admin/stock/movements?tipo=devolucion", headers=_admin_headers(client, admin))
    assert resp4.status_code == 200
    devoluciones = [m for m in resp4.json()["items"] if m["pedido_id"] == order["id"]]
    assert devoluciones, "no hay movimiento devolucion del rechazo"

    # Filtro tipo inválido → 422
    resp5 = client.get("/admin/stock/movements?tipo=otro", headers=_admin_headers(client, admin))
    assert resp5.status_code == 422


# ---------------------------------------------------------------------------
# A-FAC-01/02 — GET /admin/invoices, GET /admin/invoices/{id}
# ---------------------------------------------------------------------------


def test_invoices_list_and_detail(client, admin, comprador, categoria, unidad, vendedor):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    vendedor_headers = admin_auth_header(client, vendedor.email)
    order = _create_order(client, comprador, prod, cantidad="2")
    oc_id = client.post(f"/admin/orders/{order['id']}/accept", headers=vendedor_headers).json()["orden_compra"]["id"]
    resp_fac = client.post(f"/admin/orders/{order['id']}/facturar", headers=_admin_headers(client, admin))
    assert resp_fac.status_code == 200, resp_fac.text
    factura = resp_fac.json()["factura"]

    resp = client.get("/admin/invoices", headers=_admin_headers(client, admin))
    assert resp.status_code == 200, resp.text
    listing = resp.json()
    assert listing["total"] >= 1
    assert any(i["id"] == factura["id"] for i in listing["items"])

    resp2 = client.get(f"/admin/invoices?orden_compra_id={oc_id}", headers=_admin_headers(client, admin))
    assert resp2.status_code == 200
    filtered = resp2.json()
    assert filtered["total"] == 1 and filtered["items"][0]["id"] == factura["id"]

    resp3 = client.get(f"/admin/invoices/{factura['id']}", headers=_admin_headers(client, admin))
    assert resp3.status_code == 200, resp3.text
    detail = resp3.json()
    assert detail["numero_fiscal"] == factura["numero_fiscal"]
    assert detail["orden_compra"]["id"] == oc_id
    assert any(p["id"] == order["id"] for p in detail["pedidos"])

    resp4 = client.get(f"/admin/invoices/{uuid.uuid4()}", headers=_admin_headers(client, admin))
    assert resp4.status_code == 404


# ---------------------------------------------------------------------------
# A-AUD-01 — GET /admin/audit (transiciones auditadas + permisos)
# ---------------------------------------------------------------------------


def test_audit_accept_transition_and_reassign_antes_despues(client, admin, vendedor, comprador, categoria, unidad, db_session):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    vendedor_headers = admin_auth_header(client, vendedor.email)

    # Pedido pendiente con vendedor1 asignado (creado en su nombre)
    resp = client.post(
        "/admin/orders",
        json={"user_id": str(comprador.id), "items": [{"product_id": prod["id"], "cantidad": "1"}]},
        headers=vendedor_headers,
    )
    assert resp.status_code == 201, resp.text
    order = resp.json()

    # Reasignación pendiente → vendedor2, con antes/después (TC-RN27-02)
    from app.models.user import User
    from app.core.security import hash_password

    vendedor2 = User(
        email=f"vendedor2_{uuid.uuid4().hex[:6]}@test.com",
        display_name="Vendedor 2",
        password_hash=hash_password("Abcdef1!"),
        role="vendedor",
        is_active=True,
    )
    db_session.add(vendedor2)
    db_session.commit()

    resp2 = client.patch(
        f"/admin/orders/{order['id']}/reassign",
        json={"to_vendedor_id": str(vendedor2.id)},
        headers=_admin_headers(client, admin),
    )
    assert resp2.status_code == 200, resp2.text
    assert resp2.json()["vendedor_id"] == str(vendedor2.id)

    # Transición aceptar por vendedor2 → auditada (TC-AUD-01)
    resp3 = client.post(f"/admin/orders/{order['id']}/accept", headers=admin_auth_header(client, vendedor2.email))
    assert resp3.status_code == 200, resp3.text

    rows = _audit_rows(client, admin, entidad="pedido")
    aceptar = [r for r in rows if r["accion"] == "pedido.aceptar" and r["entidad_id"] == order["id"]]
    assert aceptar, "falta auditoría pedido.aceptar"
    assert aceptar[0]["actor_id"] == str(vendedor2.id)
    assert aceptar[0]["datos_antes"]["estado"] == "pendiente"
    assert aceptar[0]["datos_despues"]["estado"] == "aceptado"

    rows2 = _audit_rows(client, admin, entidad="pedido")
    reasignar = [r for r in rows2 if r["accion"] == "pedido.reasignar" and r["entidad_id"] == order["id"]]
    assert reasignar, "falta auditoría pedido.reasignar"
    assert reasignar[0]["datos_antes"]["vendedor_id"] == str(vendedor.id)
    assert reasignar[0]["datos_despues"]["vendedor_id"] == str(vendedor2.id)


def test_audit_permissions_admin_only(client, admin, vendedor, comprador):
    # Comprador con token de tienda → 401 (audiencia store no abre superficie admin)
    store_headers = auth_client_for(client, comprador)
    resp = client.get("/admin/audit", headers=store_headers)
    assert resp.status_code in (401, 403)

    # Vendedor (aud admin) autenticado pero sin rol administrador → 403
    vendedor_headers = admin_auth_header(client, vendedor.email)
    resp2 = client.get("/admin/audit", headers=vendedor_headers)
    assert resp2.status_code == 403

    # Administrador → 200
    resp3 = client.get("/admin/audit", headers=_admin_headers(client, admin))
    assert resp3.status_code == 200


def test_audit_filters_and_newest_first(client, admin):
    headers = _admin_headers(client, admin)
    # Genera dos filas de auditoría distintas
    resp = client.post(
        "/colecciones",
        json={"nombre": "Aud Filtro", "slug": f"aud-filtro-{uuid.uuid4().hex[:6]}", "destacada": False},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    col_id = resp.json()["id"]
    client.patch(f"/colecciones/{col_id}/destacada", json={"destacada": True}, headers=headers)

    rows = _audit_rows(client, admin, entidad="coleccion")
    assert rows, "no hay filas de auditoría de colección"
    # Orden descendente por created_at (más nuevo primero)
    fechas = [r["created_at"] for r in rows]
    assert fechas == sorted(fechas, reverse=True)

    # Filtro por actor_id
    rows_actor = _audit_rows(client, admin, actor_id=str(admin.id))
    assert rows_actor and all(r["actor_id"] == str(admin.id) for r in rows_actor)

    # Filtro por rango de fechas (desde hoy)
    from datetime import date

    rows_from = _audit_rows(client, admin, **{"from": date.today().isoformat()})
    assert rows_from, "filtro from no devuelve filas de hoy"
