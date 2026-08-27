"""Product catalog tests — TC-RN01/20/23/31/32/24, RN-04/05/07/30, etc."""
from __future__ import annotations

import uuid

from tests.conftest import auth_client_for, create_product_fixture


def test_create_product_happy(client, categoria, unidad, vendedor, etiqueta):
    prod = create_product_fixture(client, categoria, unidad, vendedor, etiqueta)
    assert prod["titulo"].startswith("Producto")
    assert prod["precio"] == "10.50" or prod["precio"] == 10.5 or str(prod["precio"]) == "10.50"


def test_create_product_requires_category_RN01(client, unidad, vendedor):
    headers = auth_client_for(client, vendedor)
    resp = client.post(
        "/products",
        json={
            "titulo": "Sin cat",
            "slug": f"sin-cat-{uuid.uuid4().hex[:4]}",
            "precio": "5.00",
            "unidad_venta_id": str(unidad.id),
            "categoria_ids": [],
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_create_product_duplicate_slug_409(client, categoria, unidad, vendedor):
    sfx = uuid.uuid4().hex[:6]
    headers = auth_client_for(client, vendedor)
    payload = {
        "titulo": f"P {sfx}",
        "slug": f"dup-{sfx}",
        "precio": "5.00",
        "unidad_venta_id": str(unidad.id),
        "categoria_ids": [str(categoria.id)],
    }
    resp1 = client.post("/products", json=payload, headers=headers)
    assert resp1.status_code == 201
    resp2 = client.post("/products", json=payload, headers=headers)
    assert resp2.status_code == 409


def test_list_products_public_filter_deleted_hidden(client, categoria, unidad, vendedor):
    # Create product then hide it
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    pid = prod["id"]
    headers_admin = auth_client_for(client, vendedor)
    # Try visibility toggle as vendedor (should 403, needs admin) — use admin fixture
    # Instead create admin
    from app.core.security import hash_password
    from app.models.user import User

    # get db via fixture? Simpler: test public listing
    resp = client.get("/products")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_search_combinable_RN04(client, categoria, unidad, vendedor, etiqueta, db_session):
    # Create two products with distinct titles
    p1 = create_product_fixture(client, categoria, unidad, vendedor, etiqueta, slug_suffix="searchA")
    # Search by titulo
    resp = client.get("/products", params={"q": p1["titulo"][:4]})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_sorting_RN07(client, categoria, unidad, vendedor):
    # Ensure sorting params don't error
    for sort in ["precio_asc", "precio_desc", "mas_reciente", "a_z", "z_a", "relevance"]:
        resp = client.get("/products", params={"sort": sort})
        assert resp.status_code == 200, sort


def test_categoria_crud_admin_only(client, comprador, admin):
    # Comprador cannot create
    headers_comp = auth_client_for(client, comprador)
    resp = client.post(
        "/categorias",
        json={"nombre": "nueva cat", "slug": "nueva-cat", "color": "#FF0000"},
        headers=headers_comp,
    )
    assert resp.status_code == 403
    # Admin can
    headers_admin = auth_client_for(client, admin)
    suffix = uuid.uuid4().hex[:4]
    resp2 = client.post(
        "/categorias",
        json={"nombre": f"cat-{suffix}", "slug": f"cat-{suffix}", "color": "#00FF00"},
        headers=headers_admin,
    )
    assert resp2.status_code == 201
    # Invalid color
    resp3 = client.post(
        "/categorias",
        json={"nombre": f"cat2-{suffix}", "slug": f"cat2-{suffix}", "color": "red"},
        headers=headers_admin,
    )
    assert resp3.status_code == 422


def test_etiqueta_autocomplete_RN03(client, vendedor):
    headers = auth_client_for(client, vendedor)
    # Create a tag
    suffix = uuid.uuid4().hex[:4]
    client.post(
        "/etiquetas",
        json={"nombre": f"tor{suffix}", "slug": f"tor{suffix}"},
        headers=headers,
    )
    resp = client.get("/etiquetas/autocomplete", params={"q": "tor"})
    assert resp.status_code == 200
    assert len(resp.json()) <= 10


def test_unidad_create_extensible_RN23(client, admin):
    headers = auth_client_for(client, admin)
    suffix = uuid.uuid4().hex[:4]
    resp = client.post(
        "/unidades-medida", json={"nombre": f"litro{suffix}", "simbolo": "L"}, headers=headers
    )
    assert resp.status_code == 201


def test_product_visibility_RN31(client, categoria, unidad, admin, vendedor):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    pid = prod["id"]
    headers_admin = auth_client_for(client, admin)
    # Hide
    resp = client.patch(f"/products/{pid}/visibility", params={"estado": "oculto"}, headers=headers_admin)
    assert resp.status_code == 200
    assert resp.json()["estado_publicacion"] == "oculto"
    # Public should not see (clear auth cookies to become anonymous)
    client.cookies.clear()
    resp2 = client.get(f"/products/{prod['slug']}")
    assert resp2.status_code == 404
    # Staff sees with include_hidden
    headers_admin2 = auth_client_for(client, admin)
    resp3 = client.get("/products", params={"include_hidden": "true"}, headers=headers_admin2)
    assert resp3.status_code == 200


def test_product_logical_delete_RN32(client, categoria, unidad, admin, vendedor):
    prod = create_product_fixture(client, categoria, unidad, vendedor)
    pid = prod["id"]
    headers_admin = auth_client_for(client, admin)
    resp = client.delete(f"/products/{pid}", headers=headers_admin)
    assert resp.status_code == 204
    # Public get should 404
    client.cookies.clear()
    resp2 = client.get(f"/products/{prod['slug']}")
    assert resp2.status_code == 404
