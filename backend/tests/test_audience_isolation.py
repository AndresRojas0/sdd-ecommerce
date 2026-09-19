"""TC-AUTH10-01 — JWT audience isolation (ADR-003/005).

The store and admin surfaces must not accept each other's tokens:
distinct secrets, distinct cookie names, distinct refresh families.
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models.refresh_token import RefreshToken
from tests.conftest import create_product_fixture

PASSWORD = "Abcdef1!"


def _admin_login(client: TestClient, email: str, password: str = PASSWORD):
    return client.post("/admin/auth/login", json={"email": email, "password": password})


def _store_login(client: TestClient, email: str, password: str = PASSWORD):
    return client.post("/auth/login", json={"email": email, "password": password})


# ---------------------------------------------------------------------------
# Admin login: cookies, paths, store-cookie absence
# ---------------------------------------------------------------------------


def test_admin_login_sets_admin_cookies_and_paths(client, admin):
    resp = _admin_login(client, admin.email)
    assert resp.status_code == 200, resp.text
    assert resp.cookies.get("admin_access_token") is not None
    assert resp.cookies.get("admin_refresh_token") is not None
    # The admin surface must not issue store cookies
    assert resp.cookies.get("access_token") is None
    assert resp.cookies.get("refresh_token") is None
    refresh_sets = [
        c for c in resp.headers.get_list("set-cookie") if c.lower().startswith("admin_refresh_token=")
    ]
    assert refresh_sets, resp.headers.get_list("set-cookie")
    assert "path=/admin/auth/refresh" in refresh_sets[0].lower()


# ---------------------------------------------------------------------------
# Token scoping across surfaces
# ---------------------------------------------------------------------------


def test_admin_token_works_on_admin_users(client, admin):
    resp = _admin_login(client, admin.email)
    assert resp.status_code == 200, resp.text
    resp_users = client.get("/admin/users")
    assert resp_users.status_code == 200, resp_users.text
    assert resp_users.json()["total"] >= 1


def test_admin_token_rejected_on_store_surface(client, admin):
    resp = _admin_login(client, admin.email)
    admin_token = resp.cookies["admin_access_token"]
    # Force the admin JWT into the store cookie slot: the store secret must reject it.
    resp_users_me = client.get("/users/me", cookies={"access_token": admin_token})
    assert resp_users_me.status_code == 401
    resp_auth_me = client.get("/auth/me", cookies={"access_token": admin_token})
    assert resp_auth_me.status_code == 401


def test_store_token_rejected_on_admin_surface(client, comprador):
    resp = _store_login(client, comprador.email)
    assert resp.status_code == 200, resp.text
    store_token = resp.cookies["access_token"]
    # Store JWT in the admin cookie slot: the admin secret must reject it.
    resp_users = client.get("/admin/users", cookies={"admin_access_token": store_token})
    assert resp_users.status_code == 401
    resp_me = client.get("/admin/auth/me", cookies={"admin_access_token": store_token})
    assert resp_me.status_code == 401


def test_comprador_credentials_rejected_on_admin_login(client, comprador):
    # Valid credentials, but the role is not staff: 403 (role, not existence).
    resp = _admin_login(client, comprador.email)
    assert resp.status_code == 403
    assert resp.cookies.get("admin_access_token") is None


# ---------------------------------------------------------------------------
# Refresh-token audience isolation
# ---------------------------------------------------------------------------


def test_admin_refresh_token_rejected_on_store_refresh(client, admin):
    resp = _admin_login(client, admin.email)
    assert resp.status_code == 200, resp.text
    admin_refresh = resp.cookies["admin_refresh_token"]

    # Admin refresh token on the store endpoint → 401 (aud mismatch)
    resp_cross = client.post("/auth/refresh", cookies={"refresh_token": admin_refresh})
    assert resp_cross.status_code == 401

    # Cross-surface probe must not have touched the admin family
    resp_admin = client.post("/admin/auth/refresh")
    assert resp_admin.status_code == 200, resp_admin.text


def test_store_refresh_token_rejected_on_admin_refresh(client, comprador):
    resp = _store_login(client, comprador.email)
    assert resp.status_code == 200, resp.text
    store_refresh = resp.cookies["refresh_token"]

    resp_cross = client.post("/admin/auth/refresh", cookies={"admin_refresh_token": store_refresh})
    assert resp_cross.status_code == 401

    # Store family survives
    resp_store = client.post("/auth/refresh")
    assert resp_store.status_code == 200, resp_store.text


# ---------------------------------------------------------------------------
# Admin full cycle: login → me → refresh rotation → logout → family revoked
# ---------------------------------------------------------------------------


def test_admin_full_cycle_login_me_refresh_logout(client, admin, db_session):
    resp = _admin_login(client, admin.email)
    assert resp.status_code == 200, resp.text

    resp_me = client.get("/admin/auth/me")
    assert resp_me.status_code == 200, resp_me.text
    assert resp_me.json()["email"] == admin.email

    # Refresh rotation within the admin audience
    old_refresh = resp.cookies["admin_refresh_token"]
    resp_ref = client.post("/admin/auth/refresh")
    assert resp_ref.status_code == 200, resp_ref.text
    new_refresh = resp_ref.cookies.get("admin_refresh_token")
    assert new_refresh is not None and new_refresh != old_refresh

    # Logout clears admin cookies and revokes the admin rows
    resp_out = client.post("/admin/auth/logout")
    assert resp_out.status_code == 200, resp_out.text
    cleared = {c.split("=", 1)[0].strip().lower() for c in resp_out.headers.get_list("set-cookie")}
    assert "admin_access_token" in cleared
    assert "admin_refresh_token" in cleared

    # Family revoked: replaying the rotated refresh must fail
    resp_replay = client.post("/admin/auth/refresh", cookies={"admin_refresh_token": new_refresh})
    assert resp_replay.status_code == 401

    rows = db_session.scalars(select(RefreshToken).where(RefreshToken.user_id == admin.id)).all()
    assert rows
    assert all(r.revoked for r in rows)
    assert all(r.aud == "admin" for r in rows)


# ---------------------------------------------------------------------------
# Password changes
# ---------------------------------------------------------------------------


def test_change_password_revokes_both_audiences(client, admin, db_session):
    """Store change-password must revoke ALL the user's refresh rows (ADR-005)."""
    resp_store = _store_login(client, admin.email)
    assert resp_store.status_code == 200, resp_store.text
    resp_admin = _admin_login(client, admin.email)
    assert resp_admin.status_code == 200, resp_admin.text
    admin_refresh = resp_admin.cookies["admin_refresh_token"]

    resp_change = client.post(
        "/auth/change-password",
        json={"current_password": PASSWORD, "new_password": "Nuevo123!"},
    )
    assert resp_change.status_code == 200, resp_change.text

    rows = db_session.scalars(select(RefreshToken).where(RefreshToken.user_id == admin.id)).all()
    assert rows
    assert all(r.revoked for r in rows)
    assert {r.aud for r in rows} == {"store", "admin"}

    # The admin refresh family is dead too
    client.cookies.clear()
    resp_replay = client.post("/admin/auth/refresh", cookies={"admin_refresh_token": admin_refresh})
    assert resp_replay.status_code == 401


def test_admin_change_password_force_rotates_credentials(client, admin, db_session):
    resp = _admin_login(client, admin.email)
    assert resp.status_code == 200, resp.text
    old_refresh = resp.cookies["admin_refresh_token"]

    resp_change = client.post(
        "/admin/auth/change-password-force",
        json={"current_password": PASSWORD, "new_password": "Nuevo456!"},
    )
    assert resp_change.status_code == 200, resp_change.text

    # All refresh rows revoked, across both audiences
    rows = db_session.scalars(select(RefreshToken).where(RefreshToken.user_id == admin.id)).all()
    assert rows
    assert all(r.revoked for r in rows)

    # Old refresh is dead
    resp_replay = client.post("/admin/auth/refresh", cookies={"admin_refresh_token": old_refresh})
    assert resp_replay.status_code == 401

    # Old password rejected, new password works on the admin surface
    resp_old = _admin_login(client, admin.email)
    assert resp_old.status_code == 401
    resp_new = _admin_login(client, admin.email, "Nuevo456!")
    assert resp_new.status_code == 200, resp_new.text


# ---------------------------------------------------------------------------
# TC-AUTH10-02 — admin-designated ops enforce the admin audience (ADR-005)
# One representative op per router group.
# ---------------------------------------------------------------------------

_ADMIN_OP_CASES = [
    "orders",
    "products",
    "categorias",
    "etiquetas",
    "unidades",
    "colecciones",
    "stock",
    "dashboard",
]


def _admin_op_case(case: str, *, client: TestClient, categoria, unidad, vendedor, comprador):
    """Return (method, url, json_body, expected_ok_status) for the representative op."""
    sfx = uuid.uuid4().hex[:6]
    if case == "orders":
        prod = create_product_fixture(client, categoria, unidad, vendedor)
        return (
            "POST",
            "/admin/orders",
            {"user_id": str(comprador.id), "items": [{"product_id": prod["id"], "cantidad": "1"}]},
            201,
        )
    if case == "products":
        # Requires a valid unidad_medida + categoria (childless root is allowed, RN-38 MVP fallback)
        return (
            "POST",
            "/products",
            {
                "titulo": f"Prod {sfx}",
                "slug": f"prod-{sfx}",
                "descripcion": "desc",
                "precio": "10.50",
                "unidad_venta_id": str(unidad.id),
                "categoria_ids": [str(categoria.id)],
            },
            201,
        )
    if case == "categorias":
        return ("POST", "/categorias", {"nombre": f"cat-{sfx}", "slug": f"cat-{sfx}", "color": "#112233"}, 201)
    if case == "etiquetas":
        return ("POST", "/etiquetas", {"nombre": f"tag-{sfx}", "slug": f"tag-{sfx}"}, 201)
    if case == "unidades":
        return ("POST", "/unidades-medida", {"nombre": f"unidad-{sfx}", "simbolo": "X"}, 201)
    if case == "colecciones":
        return ("POST", "/colecciones", {"nombre": f"col-{sfx}", "slug": f"col-{sfx}"}, 201)
    if case == "stock":
        prod = create_product_fixture(client, categoria, unidad, vendedor)
        return ("PUT", f"/admin/stock/{prod['id']}", {"cantidad_disponible": "50"}, 200)
    if case == "dashboard":
        return ("GET", "/admin/dashboard/totales-hoy", None, 200)
    raise ValueError(f"unknown case: {case}")


@pytest.mark.parametrize("case", _ADMIN_OP_CASES)
def test_admin_ops_reject_store_token_and_accept_admin_token(
    client, admin, comprador, vendedor, categoria, unidad, case
):
    """A store-aud comprador token via the standard store cookie name must be
    rejected (401/403). The same op with an admin-aud token via the admin
    cookie must pass auth — it may only fail on business validation (never
    401/403) and succeeds outright for these valid bodies."""
    method, url, body, ok_status = _admin_op_case(
        case, client=client, categoria=categoria, unidad=unidad, vendedor=vendedor, comprador=comprador
    )

    # 1) Store-aud token in the standard store cookie name → rejected.
    resp_store = _store_login(client, comprador.email)
    assert resp_store.status_code == 200, resp_store.text
    store_token = resp_store.cookies["access_token"]
    client.cookies.clear()  # no admin-aud cookie may leak into this probe
    reject_kwargs: dict = {"cookies": {"access_token": store_token}}
    if body is not None:
        reject_kwargs["json"] = body
    resp_rejected = client.request(method, url, **reject_kwargs)
    assert resp_rejected.status_code in (401, 403), resp_rejected.text

    # 2) Admin-aud token via the admin cookie → auth passes.
    client.cookies.clear()
    resp_admin = _admin_login(client, admin.email)
    assert resp_admin.status_code == 200, resp_admin.text
    ok_kwargs: dict = {}
    if body is not None:
        ok_kwargs["json"] = body
    resp_ok = client.request(method, url, **ok_kwargs)
    assert resp_ok.status_code not in (401, 403), resp_ok.text
    assert resp_ok.status_code == ok_status, resp_ok.text
