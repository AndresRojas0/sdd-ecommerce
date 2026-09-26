"""User lifecycle from the admin panel — A-USR-07/08/09 + first-login flow (BOOT-03).

Covers: create user with temp password (auto or provided), password reset
revoking refresh rows (both audiences), role change (audited, self-guard),
and audience/role gates on the three new endpoints.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select

from app.core.security import hash_password
from app.models.refresh_token import RefreshToken
from app.models.user import User
from tests.conftest import admin_auth_header, auth_header


def _admin_headers(client, admin) -> dict:
    return admin_auth_header(client, admin.email)


def _audit_rows(client, admin, accion: str) -> list[dict]:
    resp = client.get("/admin/audit", params={"accion": accion}, headers=_admin_headers(client, admin))
    assert resp.status_code == 200, resp.text
    return resp.json()["items"]


# ---------------------------------------------------------------------------
# A-USR-07 — POST /admin/users
# ---------------------------------------------------------------------------


def test_create_vendedor_auto_temp_password(client, admin, db_session):
    headers = _admin_headers(client, admin)
    email = f"nuevo_vend_{uuid.uuid4().hex[:6]}@test.com"
    resp = client.post(
        "/admin/users",
        json={"email": email, "display_name": "Vendedor Nuevo", "role": "vendedor"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    # Temp password: solo en esta respuesta, policy-compliant por construcción
    assert data["temp_password"].startswith("Tp-") and data["temp_password"].endswith("!7A")
    assert len(data["temp_password"]) >= 8
    assert data["aviso"] == "Mostrar una sola vez"
    # User payload
    assert data["user"]["email"] == email
    assert data["user"]["role"] == "vendedor"
    assert data["user"]["is_active"] is True
    assert data["user"]["must_change_password"] is True
    # La contraseña nunca viaja en el payload del usuario
    assert "password" not in data["user"]
    # La raw temp password NO se persiste ni se audita
    user = db_session.scalar(select(User).where(User.email == email))
    assert user is not None
    assert user.password_hash != data["temp_password"]
    rows = _audit_rows(client, admin, "usuario.crear")
    match = [r for r in rows if r["entidad_id"] == str(user.id)]
    assert match, "falta auditoría usuario.crear"
    assert match[0]["datos_despues"]["email"] == email
    assert match[0]["datos_despues"]["role"] == "vendedor"
    assert "temp_password" not in match[0]["datos_despues"]


def test_create_user_rejects_duplicate_email_weak_temp_and_admin_role(client, admin):
    headers = _admin_headers(client, admin)
    # RN-14: email duplicado
    resp = client.post(
        "/admin/users",
        json={"email": admin.email, "display_name": "Dup", "role": "comprador"},
        headers=headers,
    )
    assert resp.status_code == 422
    # AUTH-04: temp_password provista que viola la política
    resp2 = client.post(
        "/admin/users",
        json={
            "email": f"weak_{uuid.uuid4().hex[:6]}@test.com",
            "display_name": "Weak",
            "role": "vendedor",
            "temp_password": "debil",
        },
        headers=headers,
    )
    assert resp2.status_code == 422
    # El panel NO crea administradores
    resp3 = client.post(
        "/admin/users",
        json={
            "email": f"admin_{uuid.uuid4().hex[:6]}@test.com",
            "display_name": "Admin desde panel",
            "role": "administrador",
        },
        headers=headers,
    )
    assert resp3.status_code == 422


# ---------------------------------------------------------------------------
# First-login flow (BOOT-03): temp → 403 MUST_CHANGE_PASSWORD → force change
# ---------------------------------------------------------------------------


def test_first_login_flow_forced_change(client, admin):
    headers = _admin_headers(client, admin)
    email = f"primer_login_{uuid.uuid4().hex[:6]}@test.com"
    temp = "Temporal1!"
    resp = client.post(
        "/admin/users",
        json={"email": email, "display_name": "Primer Login", "role": "vendedor", "temp_password": temp},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text

    # 1) Login con la temporal → 403 MUST_CHANGE_PASSWORD pero CON cookies admin
    client.cookies.clear()
    login1 = client.post("/admin/auth/login", json={"email": email, "password": temp})
    assert login1.status_code == 403, login1.text
    body1 = login1.json()
    assert body1["detail"]["code"] == "MUST_CHANGE_PASSWORD"
    assert login1.cookies.get("admin_access_token") is not None

    # 2) change-password-force con la sesión del 403
    force = client.post(
        "/admin/auth/change-password-force",
        json={"current_password": temp, "new_password": "NuevaClave1!"},
    )
    assert force.status_code == 200, force.text

    # 3) La temporal quedó muerta
    client.cookies.clear()
    login_old = client.post("/admin/auth/login", json={"email": email, "password": temp})
    assert login_old.status_code == 401

    # 4) La nueva entra y /admin/auth/me refleja el rol asignado
    login2 = client.post("/admin/auth/login", json={"email": email, "password": "NuevaClave1!"})
    assert login2.status_code == 200, login2.text
    me = client.get("/admin/auth/me")
    assert me.status_code == 200, me.text
    assert me.json()["role"] == "vendedor"
    assert me.json()["email"] == email


# ---------------------------------------------------------------------------
# A-USR-08 — POST /admin/users/{user_id}/password-reset
# ---------------------------------------------------------------------------


def test_reset_password_kills_old_credentials_and_revokes_sessions(client, admin, comprador, db_session):
    # Sesión previa del comprador (store) → crea fila de refresh aud tienda
    auth_header(client, comprador.email)
    refresh_rows_before = db_session.scalars(
        select(RefreshToken).where(RefreshToken.user_id == comprador.id, RefreshToken.revoked.is_(False))
    ).all()
    assert refresh_rows_before, "el login previo debería haber creado refresh rows"

    headers = _admin_headers(client, admin)
    resp = client.post(f"/admin/users/{comprador.id}/password-reset", json={}, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["temp_password"].startswith("Tp-") and data["aviso"] == "Mostrar una sola vez"

    # Todas las filas de refresh (ambas audiencias) quedaron revocadas
    db_session.expire_all()
    remaining = db_session.scalars(
        select(RefreshToken).where(RefreshToken.user_id == comprador.id, RefreshToken.revoked.is_(False))
    ).all()
    assert remaining == []

    # La contraseña vieja ya no sirve en la tienda
    old_login = client.post("/auth/login", json={"email": comprador.email, "password": "Abcdef1!"})
    assert old_login.status_code == 401

    # La temporal entra PERO con cambio forzado: para un comprador la
    # superficie válida es la tienda (el admin login rechaza por rol antes
    # del check must_change_password).
    client.cookies.clear()
    temp_login = client.post(
        "/auth/login", json={"email": comprador.email, "password": data["temp_password"]}
    )
    assert temp_login.status_code == 403, temp_login.text
    assert temp_login.json()["detail"]["code"] == "MUST_CHANGE_PASSWORD"

    # Auditoría
    rows = _audit_rows(client, admin, "usuario.reset_password")
    match = [r for r in rows if r["entidad_id"] == str(comprador.id)]
    assert match, "falta auditoría usuario.reset_password"

    # Usuario inexistente → 404
    resp404 = client.post(f"/admin/users/{uuid.uuid4()}/password-reset", json={}, headers=headers)
    assert resp404.status_code == 404


def test_reset_password_works_on_other_admin_and_weak_temp_rejected(client, admin, db_session):
    other_admin = User(
        email=f"other_admin_{uuid.uuid4().hex[:6]}@test.com",
        display_name="Otro Admin",
        password_hash=hash_password("Abcdef1!"),
        role="administrador",
        is_active=True,
    )
    db_session.add(other_admin)
    db_session.commit()
    db_session.refresh(other_admin)

    headers = _admin_headers(client, admin)
    # Temp débil → 422 (AUTH-04)
    resp_weak = client.post(
        f"/admin/users/{other_admin.id}/password-reset",
        json={"temp_password": "corta1!"},
        headers=headers,
    )
    assert resp_weak.status_code == 422

    # Reset sobre OTRO administrador: permitido
    resp = client.post(f"/admin/users/{other_admin.id}/password-reset", json={}, headers=headers)
    assert resp.status_code == 200, resp.text
    temp = resp.json()["temp_password"]
    client.cookies.clear()
    temp_login = client.post("/admin/auth/login", json={"email": other_admin.email, "password": temp})
    assert temp_login.status_code == 403
    assert temp_login.json()["detail"]["code"] == "MUST_CHANGE_PASSWORD"


# ---------------------------------------------------------------------------
# A-USR-09 — PATCH /admin/users/{user_id}/role
# ---------------------------------------------------------------------------


def test_role_change_ok_and_audited(client, admin, comprador):
    headers = _admin_headers(client, admin)
    resp = client.patch(f"/admin/users/{comprador.id}/role", json={"role": "vendedor"}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["role"] == "vendedor"

    rows = _audit_rows(client, admin, "usuario.cambiar_rol")
    match = [r for r in rows if r["entidad_id"] == str(comprador.id)]
    assert match, "falta auditoría usuario.cambiar_rol"
    assert match[0]["datos_antes"]["role"] == "comprador"
    assert match[0]["datos_despues"]["role"] == "vendedor"

    # role=administrador no es asignable desde el panel
    resp2 = client.patch(f"/admin/users/{comprador.id}/role", json={"role": "administrador"}, headers=headers)
    assert resp2.status_code == 422

    # Usuario inexistente → 404
    resp404 = client.patch(f"/admin/users/{uuid.uuid4()}/role", json={"role": "vendedor"}, headers=headers)
    assert resp404.status_code == 404


def test_role_change_own_account_rejected(client, admin):
    headers = _admin_headers(client, admin)
    resp = client.patch(f"/admin/users/{admin.id}/role", json={"role": "vendedor"}, headers=headers)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Gates de audiencia y rol en los tres endpoints nuevos
# ---------------------------------------------------------------------------


def test_gates_comprador_store_token_401_and_vendedor_admin_token_403(
    client, admin, comprador, vendedor, db_session
):
    email = f"gate_{uuid.uuid4().hex[:6]}@test.com"
    create_body = {"email": email, "display_name": "Gate", "role": "vendedor"}

    # Token de tienda (comprador) contra la superficie admin → 401
    store_headers = auth_header(client, comprador.email)
    resp_create = client.post("/admin/users", json=create_body, headers=store_headers)
    assert resp_create.status_code == 401
    resp_reset = client.post(f"/admin/users/{comprador.id}/password-reset", json={}, headers=store_headers)
    assert resp_reset.status_code == 401
    resp_role = client.patch(f"/admin/users/{comprador.id}/role", json={"role": "vendedor"}, headers=store_headers)
    assert resp_role.status_code == 401

    # Token admin-aud de vendedor: autenticado pero sin rol `administrador` → 403
    vend_headers = admin_auth_header(client, vendedor.email)
    resp_create2 = client.post("/admin/users", json=create_body, headers=vend_headers)
    assert resp_create2.status_code == 403
    resp_reset2 = client.post(f"/admin/users/{comprador.id}/password-reset", json={}, headers=vend_headers)
    assert resp_reset2.status_code == 403
    resp_role2 = client.patch(f"/admin/users/{comprador.id}/role", json={"role": "vendedor"}, headers=vend_headers)
    assert resp_role2.status_code == 403
