"""Categories tree 2 levels + collections (RN-01, RN-38, RN-39).

Revision ID: 003_categories_tree_collections
Revises: 002_extended_flow
Create Date: 2026-09-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_categories_tree_collections"
down_revision: Union[str, None] = "002_extended_flow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else "postgresql"
    is_sqlite = dialect == "sqlite"

    # --- Alter categorias: add parent_id, nivel, updated_at ---
    if is_sqlite:
        with op.batch_alter_table("categorias", recreate="auto") as batch_op:
            batch_op.add_column(sa.Column("parent_id", sa.String(length=36), nullable=True))
            batch_op.add_column(sa.Column("nivel", sa.SmallInteger(), nullable=False, server_default=sa.text("1")))
            batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
            batch_op.create_index("idx_categorias_parent_id", ["parent_id"])
        op.execute(sa.text("UPDATE categorias SET nivel = 1 WHERE nivel IS NULL"))
        op.execute(sa.text("UPDATE categorias SET parent_id = NULL WHERE parent_id IS NOT NULL AND parent_id = ''"))
    else:
        op.add_column("categorias", sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categorias.id", ondelete="RESTRICT"), nullable=True))
        op.add_column("categorias", sa.Column("nivel", sa.SmallInteger(), nullable=False, server_default=sa.text("1")))
        op.add_column("categorias", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
        op.execute(sa.text("UPDATE categorias SET nivel = 1 WHERE nivel IS NULL"))
        op.execute(sa.text("UPDATE categorias SET updated_at = created_at WHERE updated_at IS NULL"))
        op.execute(sa.text("UPDATE categorias SET nivel = 1, parent_id = NULL WHERE true"))
        op.create_index("idx_categorias_parent_id", "categorias", ["parent_id"])
        op.execute(sa.text("ALTER TABLE categorias DROP CONSTRAINT IF EXISTS ck_categorias_nivel"))
        op.execute(sa.text("ALTER TABLE categorias ADD CONSTRAINT ck_categorias_nivel CHECK (nivel IN (1, 2))"))
        op.execute(sa.text("ALTER TABLE categorias DROP CONSTRAINT IF EXISTS ck_categorias_nivel_parent"))
        op.execute(
            sa.text(
                "ALTER TABLE categorias ADD CONSTRAINT ck_categorias_nivel_parent "
                "CHECK ((parent_id IS NULL AND nivel = 1) OR (parent_id IS NOT NULL AND nivel = 2))"
            )
        )
        op.execute(
            sa.text(
                """
                CREATE TRIGGER trg_categorias_updated_at
                BEFORE UPDATE ON categorias
                FOR EACH ROW EXECUTE FUNCTION update_updated_at();
                """
            )
        )
        op.execute(
            sa.text(
                """
                CREATE OR REPLACE FUNCTION check_categoria_parent()
                RETURNS TRIGGER AS $$
                DECLARE
                    parent_nivel SMALLINT;
                BEGIN
                    IF NEW.parent_id IS NOT NULL THEN
                        IF NEW.parent_id = NEW.id THEN
                            RAISE EXCEPTION 'parent_id no puede ser sí mismo';
                        END IF;
                        SELECT nivel INTO parent_nivel FROM categorias WHERE id = NEW.parent_id;
                        IF NOT FOUND THEN
                            RAISE EXCEPTION 'parent_id % no existe', NEW.parent_id;
                        END IF;
                        IF parent_nivel != 1 THEN
                            RAISE EXCEPTION 'parent_id debe apuntar a categoría nivel 1 (encontrado nivel %)', parent_nivel;
                        END IF;
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                """
            )
        )
        op.execute(
            sa.text(
                """
                CREATE TRIGGER trg_categorias_parent_check
                BEFORE INSERT OR UPDATE ON categorias
                FOR EACH ROW EXECUTE FUNCTION check_categoria_parent();
                """
            )
        )

    # --- Create colecciones ---
    if is_sqlite:
        op.create_table(
            "colecciones",
            sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
            sa.Column("nombre", sa.String(length=100), nullable=False),
            sa.Column("slug", sa.String(length=120), nullable=False),
            sa.Column("descripcion", sa.Text(), nullable=True),
            sa.Column("imagen", sa.String(length=500), nullable=True),
            sa.Column("destacada", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("nombre", name="uq_colecciones_nombre"),
            sa.UniqueConstraint("slug", name="uq_colecciones_slug"),
        )
        op.create_index("idx_colecciones_slug", "colecciones", ["slug"], unique=True)
        op.create_index("idx_colecciones_destacada", "colecciones", ["destacada"])
    else:
        op.create_table(
            "colecciones",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("nombre", sa.String(length=100), nullable=False),
            sa.Column("slug", sa.String(length=120), nullable=False),
            sa.Column("descripcion", sa.Text(), nullable=True),
            sa.Column("imagen", sa.String(length=500), nullable=True),
            sa.Column("destacada", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.UniqueConstraint("nombre", name="uq_colecciones_nombre"),
            sa.UniqueConstraint("slug", name="uq_colecciones_slug"),
        )
        op.create_index("idx_colecciones_slug", "colecciones", ["slug"], unique=True)
        op.execute(sa.text("CREATE INDEX idx_colecciones_destacada ON colecciones (destacada) WHERE destacada = true"))
        op.execute(
            sa.text(
                """
                CREATE TRIGGER trg_colecciones_updated_at
                BEFORE UPDATE ON colecciones
                FOR EACH ROW EXECUTE FUNCTION update_updated_at();
                """
            )
        )

    # --- Create coleccion_productos ---
    if is_sqlite:
        op.create_table(
            "coleccion_productos",
            sa.Column("coleccion_id", sa.String(length=36), sa.ForeignKey("colecciones.id", ondelete="CASCADE"), primary_key=True, nullable=False),
            sa.Column("product_id", sa.String(length=36), sa.ForeignKey("productos.id", ondelete="CASCADE"), primary_key=True, nullable=False),
            sa.Column("added_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("orden", sa.Integer(), nullable=True, server_default=sa.text("0")),
            sa.CheckConstraint("orden IS NULL OR orden >= 0", name="ck_coleccion_productos_orden"),
        )
    else:
        op.create_table(
            "coleccion_productos",
            sa.Column("coleccion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("colecciones.id", ondelete="CASCADE"), primary_key=True, nullable=False),
            sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("productos.id", ondelete="CASCADE"), primary_key=True, nullable=False),
            sa.Column("added_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("orden", sa.Integer(), nullable=True, server_default=sa.text("0")),
            sa.CheckConstraint("orden IS NULL OR orden >= 0", name="ck_coleccion_productos_orden"),
        )
    op.create_index("idx_cp_coleccion_id", "coleccion_productos", ["coleccion_id"])
    op.create_index("idx_cp_product_id", "coleccion_productos", ["product_id"])
    op.create_index("idx_cp_coleccion_orden", "coleccion_productos", ["coleccion_id", "orden"])


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else "postgresql"
    is_sqlite = dialect == "sqlite"

    op.drop_index("idx_cp_coleccion_orden", table_name="coleccion_productos")
    op.drop_index("idx_cp_product_id", table_name="coleccion_productos")
    op.drop_index("idx_cp_coleccion_id", table_name="coleccion_productos")
    op.drop_table("coleccion_productos")

    if not is_sqlite:
        op.execute(sa.text("DROP TRIGGER IF EXISTS trg_colecciones_updated_at ON colecciones"))
    op.drop_index("idx_colecciones_destacada", table_name="colecciones")
    op.drop_index("idx_colecciones_slug", table_name="colecciones")
    op.drop_table("colecciones")

    if is_sqlite:
        with op.batch_alter_table("categorias", recreate="auto") as batch_op:
            batch_op.drop_index("idx_categorias_parent_id")
            batch_op.drop_column("updated_at")
            batch_op.drop_column("nivel")
            batch_op.drop_column("parent_id")
    else:
        op.execute(sa.text("DROP TRIGGER IF EXISTS trg_categorias_parent_check ON categorias"))
        op.execute(sa.text("DROP FUNCTION IF EXISTS check_categoria_parent()"))
        op.execute(sa.text("DROP TRIGGER IF EXISTS trg_categorias_updated_at ON categorias"))
        op.execute(sa.text("ALTER TABLE categorias DROP CONSTRAINT IF EXISTS ck_categorias_nivel_parent"))
        op.execute(sa.text("ALTER TABLE categorias DROP CONSTRAINT IF EXISTS ck_categorias_nivel"))
        op.drop_index("idx_categorias_parent_id", table_name="categorias")
        op.drop_column("categorias", "updated_at")
        op.drop_column("categorias", "nivel")
        op.drop_column("categorias", "parent_id")
