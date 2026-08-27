"""Initial schema — 16 tables, extensions, GIN indexes and seeds.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extensions — idempotent
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

    # 1. users
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("avatar", sa.String(length=500), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'comprador'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "role IN ('comprador', 'vendedor', 'administrador')",
            name="ck_users_role",
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_role", "users", ["role"])
    op.create_index("idx_users_is_active", "users", ["is_active"])

    # 2. categorias
    op.create_table(
        "categorias",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("color ~ '^#[0-9A-Fa-f]{6}$'", name="ck_categorias_color"),
        sa.UniqueConstraint("nombre", name="uq_categorias_nombre"),
        sa.UniqueConstraint("slug", name="uq_categorias_slug"),
    )
    op.create_index("idx_categorias_slug", "categorias", ["slug"], unique=True)

    # 3. etiquetas
    op.create_table(
        "etiquetas",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("nombre", name="uq_etiquetas_nombre"),
        sa.UniqueConstraint("slug", name="uq_etiquetas_slug"),
    )
    op.create_index("idx_etiquetas_slug", "etiquetas", ["slug"], unique=True)
    op.create_index(
        "idx_etiquetas_nombre_trgm",
        "etiquetas",
        ["nombre"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"nombre": "gin_trgm_ops"},
    )

    # 4. unidades_medida
    op.create_table(
        "unidades_medida",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(length=50), nullable=False),
        sa.Column("simbolo", sa.String(length=10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("nombre", name="uq_unidades_medida_nombre"),
    )

    # 5. productos
    op.create_table(
        "productos",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("componentes_incluidos", sa.Text(), nullable=True),
        sa.Column(
            "datos_tecnicos",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("precio", sa.Numeric(10, 2), nullable=False),
        sa.Column("imagen", sa.String(length=500), nullable=True),
        sa.Column(
            "unidad_venta_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unidades_medida.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "estado_publicacion",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'publicado'"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "visitas_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "guardados_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "busquedas_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "calificacion_promedio",
            sa.Numeric(3, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "calificacion_cantidad",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("precio > 0", name="ck_productos_precio"),
        sa.CheckConstraint(
            "estado_publicacion IN ('publicado', 'oculto')",
            name="ck_productos_estado_publicacion",
        ),
        sa.CheckConstraint("visitas_count >= 0", name="ck_productos_visitas_count"),
        sa.CheckConstraint("guardados_count >= 0", name="ck_productos_guardados_count"),
        sa.CheckConstraint("busquedas_count >= 0", name="ck_productos_busquedas_count"),
        sa.CheckConstraint(
            "calificacion_promedio BETWEEN 0 AND 5",
            name="ck_productos_calificacion_promedio",
        ),
        sa.CheckConstraint(
            "calificacion_cantidad >= 0",
            name="ck_productos_calificacion_cantidad",
        ),
        sa.UniqueConstraint("slug", name="uq_productos_slug"),
    )
    op.create_index("idx_productos_slug", "productos", ["slug"], unique=True)
    op.create_index(
        "idx_productos_estado_publicacion", "productos", ["estado_publicacion"]
    )
    op.create_index("idx_productos_deleted_at", "productos", ["deleted_at"])
    op.create_index("idx_productos_precio", "productos", ["precio"])
    op.create_index(
        "idx_productos_created_at",
        "productos",
        [sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_productos_titulo_trgm",
        "productos",
        ["titulo"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"titulo": "gin_trgm_ops"},
    )
    op.create_index(
        "idx_productos_datos_tecnicos_gin",
        "productos",
        ["datos_tecnicos"],
        unique=False,
        postgresql_using="gin",
    )
    # Partial index for public catalog queries
    op.execute(
        sa.text(
            "CREATE INDEX idx_productos_publicos ON productos (created_at DESC) "
            "WHERE deleted_at IS NULL AND estado_publicacion = 'publicado'"
        )
    )

    # 6. producto_categorias (N:M)
    op.create_table(
        "producto_categorias",
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("productos.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "categoria_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("categorias.id", ondelete="RESTRICT"),
            primary_key=True,
            nullable=False,
        ),
    )
    op.create_index(
        "idx_pc_product_id", "producto_categorias", ["product_id"]
    )
    op.create_index(
        "idx_pc_categoria_id", "producto_categorias", ["categoria_id"]
    )

    # 7. producto_etiquetas (N:M)
    op.create_table(
        "producto_etiquetas",
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("productos.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "etiqueta_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("etiquetas.id", ondelete="RESTRICT"),
            primary_key=True,
            nullable=False,
        ),
    )
    op.create_index("idx_pt_product_id", "producto_etiquetas", ["product_id"])
    op.create_index("idx_pt_etiqueta_id", "producto_etiquetas", ["etiqueta_id"])

    # 8. favoritos
    op.create_table(
        "favoritos",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("productos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "user_id", "product_id", name="uq_favoritos_user_product"
        ),
    )
    op.create_index("idx_favoritos_user_id", "favoritos", ["user_id"])
    op.create_index("idx_favoritos_product_id", "favoritos", ["product_id"])

    # 9. visitas
    op.create_table(
        "visitas",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("productos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("visitor_cookie", sa.String(length=100), nullable=True),
        sa.Column(
            "visited_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "origen",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'directa'"),
        ),
        sa.CheckConstraint(
            "origen IN ('directa', 'busqueda')", name="ck_visitas_origen"
        ),
        sa.CheckConstraint(
            "user_id IS NOT NULL OR visitor_cookie IS NOT NULL",
            name="ck_visitas_identificador",
        ),
    )
    op.create_index(
        "idx_visitas_product_visited",
        "visitas",
        ["product_id", sa.text("visited_at DESC")],
    )
    op.create_index(
        "idx_visitas_user_product_time",
        "visitas",
        ["product_id", "user_id", "visited_at"],
    )
    op.create_index(
        "idx_visitas_cookie_product_time",
        "visitas",
        ["product_id", "visitor_cookie", "visited_at"],
    )

    # 10. calificaciones
    op.create_table(
        "calificaciones",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("productos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("estrellas", sa.SmallInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "estrellas BETWEEN 1 AND 5", name="ck_calificaciones_estrellas"
        ),
        sa.UniqueConstraint(
            "user_id", "product_id", name="uq_calificaciones_user_product"
        ),
    )
    op.create_index(
        "idx_calificaciones_product_id", "calificaciones", ["product_id"]
    )
    op.create_index("idx_calificaciones_user_id", "calificaciones", ["user_id"])

    # 11. carritos
    op.create_table(
        "carritos",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("user_id", name="uq_carritos_user_id"),
    )
    op.create_index("idx_carritos_user_id", "carritos", ["user_id"], unique=True)

    # 12. carrito_items
    op.create_table(
        "carrito_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "carrito_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("carritos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("productos.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("cantidad", sa.Numeric(10, 2), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(10, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("cantidad > 0", name="ck_carrito_items_cantidad"),
        sa.CheckConstraint(
            "precio_unitario > 0", name="ck_carrito_items_precio_unitario"
        ),
        sa.CheckConstraint("subtotal >= 0", name="ck_carrito_items_subtotal"),
        sa.UniqueConstraint(
            "carrito_id", "product_id", name="uq_carrito_items_carrito_product"
        ),
    )
    op.create_index(
        "idx_carrito_items_carrito_id", "carrito_items", ["carrito_id"]
    )
    op.create_index(
        "idx_carrito_items_product_id", "carrito_items", ["product_id"]
    )

    # 13. ordenes_compra (must precede pedidos FK)
    op.create_table(
        "ordenes_compra",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("numero", sa.String(length=30), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("total >= 0", name="ck_ordenes_compra_total"),
        sa.UniqueConstraint("numero", name="uq_ordenes_compra_numero"),
    )
    op.create_index("idx_oc_created_at", "ordenes_compra", ["created_at"])
    op.create_index("idx_oc_created_by", "ordenes_compra", ["created_by"])

    # 14. pedidos
    op.create_table(
        "pedidos",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "vendedor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "estado",
            sa.String(length=30),
            nullable=False,
            server_default=sa.text("'pendiente'"),
        ),
        sa.Column("motivo_rechazo", sa.Text(), nullable=True),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "orden_compra_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ordenes_compra.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "estado IN ('pendiente', 'aceptado', 'rechazado')",
            name="ck_pedidos_estado",
        ),
        sa.CheckConstraint(
            "motivo_rechazo IS NULL OR estado = 'rechazado'",
            name="ck_pedidos_motivo_rechazo",
        ),
        sa.CheckConstraint("subtotal >= 0", name="ck_pedidos_subtotal"),
        sa.CheckConstraint("total >= 0", name="ck_pedidos_total"),
    )
    op.create_index("idx_pedidos_user_id", "pedidos", ["user_id"])
    op.create_index("idx_pedidos_vendedor_id", "pedidos", ["vendedor_id"])
    op.create_index("idx_pedidos_estado", "pedidos", ["estado"])
    op.create_index(
        "idx_pedidos_orden_compra_id", "pedidos", ["orden_compra_id"]
    )
    op.create_index(
        "idx_pedidos_created_at",
        "pedidos",
        [sa.text("created_at DESC")],
    )
    op.create_index("idx_pedidos_user_estado", "pedidos", ["user_id", "estado"])

    # 15. pedido_items
    op.create_table(
        "pedido_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "pedido_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pedidos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("productos.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("cantidad", sa.Numeric(10, 2), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(10, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.CheckConstraint("cantidad > 0", name="ck_pedido_items_cantidad"),
        sa.CheckConstraint(
            "precio_unitario > 0", name="ck_pedido_items_precio_unitario"
        ),
        sa.CheckConstraint("subtotal >= 0", name="ck_pedido_items_subtotal"),
    )
    op.create_index("idx_pedido_items_pedido_id", "pedido_items", ["pedido_id"])
    op.create_index(
        "idx_pedido_items_product_id", "pedido_items", ["product_id"]
    )

    # 16. refresh_tokens
    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "revoked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("idx_rt_user_id", "refresh_tokens", ["user_id"])
    op.create_index("idx_rt_family_id", "refresh_tokens", ["family_id"])
    op.create_index("idx_rt_expires_at", "refresh_tokens", ["expires_at"])
    op.create_index(
        "idx_rt_token_hash", "refresh_tokens", ["token_hash"], unique=True
    )

    # Triggers for updated_at — keep updated_at = now() on UPDATE
    op.execute(
        sa.text(
            """
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
        )
    )
    for tbl in [
        "productos",
        "calificaciones",
        "carritos",
        "carrito_items",
        "pedidos",
        "ordenes_compra",
    ]:
        op.execute(
            sa.text(
                f"""
            CREATE TRIGGER trg_{tbl}_updated_at
            BEFORE UPDATE ON {tbl}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at();
            """
            )
        )

    # Seeds: unidades_medida (obligatory RN-23)
    op.execute(
        sa.text(
            """
        INSERT INTO unidades_medida (nombre, simbolo) VALUES
            ('unidades', 'u'),
            ('cm', 'cm'),
            ('m', 'm'),
            ('kg', 'kg')
        ON CONFLICT (nombre) DO NOTHING
        """
        )
    )

    # Seeds: categorias (RN-01) — 17 values, with deterministic color/slug
    op.execute(
        sa.text(
            """
        INSERT INTO categorias (nombre, slug, color) VALUES
            ('bazar', 'bazar', '#003087'),
            ('calefacción', 'calefaccion', '#CC0000'),
            ('cerrajería', 'cerrajeria', '#FF6B00'),
            ('construcción', 'construccion', '#4A4A4A'),
            ('corte', 'corte', '#007A33'),
            ('desbaste y pulido', 'desbaste-y-pulido', '#FFD700'),
            ('electricidad', 'electricidad', '#FFCC00'),
            ('fontanería', 'fontaneria', '#0055A4'),
            ('iluminación', 'iluminacion', '#FFF44F'),
            ('gas', 'gas', '#00A8E8'),
            ('herramientas', 'herramientas', '#6B4226'),
            ('materias primas', 'materias-primas', '#8B8B8B'),
            ('pintura', 'pintura', '#E4002B'),
            ('plomería', 'plomeria', '#0096C7'),
            ('refrigeración', 'refrigeracion', '#00BFFF'),
            ('sanitarios', 'sanitarios', '#2E86AB'),
            ('suministros seguridad', 'suministros-seguridad', '#FF3333')
        ON CONFLICT (nombre) DO NOTHING
        """
        )
    )

    # Seeds: etiquetas (RN-02) — common tags, subset of spec examples
    op.execute(
        sa.text(
            """
        INSERT INTO etiquetas (nombre, slug) VALUES
            ('accesorio', 'accesorio'),
            ('acero', 'acero'),
            ('aluminio', 'aluminio'),
            ('bronce', 'bronce'),
            ('cable', 'cable'),
            ('cobre', 'cobre'),
            ('disco', 'disco'),
            ('hexagonal', 'hexagonal'),
            ('inoxidable', 'inoxidable'),
            ('llave', 'llave'),
            ('madera', 'madera'),
            ('metal', 'metal'),
            ('plástico', 'plastico'),
            ('repuesto', 'repuesto'),
            ('tornillos', 'tornillos'),
            ('tuerca', 'tuerca')
        ON CONFLICT (nombre) DO NOTHING
        """
        )
    )


def downgrade() -> None:
    # Drop triggers and function
    for tbl in [
        "productos",
        "calificaciones",
        "carritos",
        "carrito_items",
        "pedidos",
        "ordenes_compra",
    ]:
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS trg_{tbl}_updated_at ON {tbl}"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS update_updated_at()"))

    # Partial index must be dropped via raw SQL (not tracked in alembic index list)
    op.execute(sa.text("DROP INDEX IF EXISTS idx_productos_publicos"))

    op.drop_table("refresh_tokens")
    op.drop_table("pedido_items")
    op.drop_table("pedidos")
    op.drop_table("ordenes_compra")
    op.drop_table("carrito_items")
    op.drop_table("carritos")
    op.drop_table("calificaciones")
    op.drop_table("visitas")
    op.drop_table("favoritos")
    op.drop_table("producto_etiquetas")
    op.drop_table("producto_categorias")
    op.drop_table("productos")
    op.drop_table("unidades_medida")
    op.drop_table("etiquetas")
    op.drop_table("categorias")
    op.drop_table("users")
    # Extensions are not dropped — shared with other schemas.

