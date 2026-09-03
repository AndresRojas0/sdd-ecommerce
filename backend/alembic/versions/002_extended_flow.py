"""Extended flow — stock + factura + estado máquina extendida (RN-28, RN-35, RN-36).

Revision ID: 002_extended_flow
Revises: 001_initial_schema
Create Date: 2026-09-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_extended_flow"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else "postgresql"
    is_sqlite = dialect == "sqlite"

    # --- Alter pedidos.estado CHECK: drop old, add new with 6 values ---
    if is_sqlite:
        # SQLite: CHECK is table-level, batch alter is safest to just keep new constraint
        # The ORM will enforce new check; existing SQLite DB will be recreated anyway in tests
        # Try to drop old check if exists and add new — SQLite may not support ALTER DROP CONSTRAINT
        # So we skip constraint manipulation for SQLite; rely on app validation
        pass
    else:
        # PostgreSQL: drop old constraint and add new
        # Constraint name is ck_pedidos_estado per model
        op.execute(sa.text("ALTER TABLE pedidos DROP CONSTRAINT IF EXISTS ck_pedidos_estado"))
        op.execute(
            sa.text(
                "ALTER TABLE pedidos ADD CONSTRAINT ck_pedidos_estado "
                "CHECK (estado IN ('pendiente', 'aceptado', 'facturado', 'en_logistica', 'entregado', 'rechazado'))"
            )
        )

    # --- Create stock ---
    op.create_table(
        "stock",
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("productos.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("cantidad_disponible", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("cantidad_reservada", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("cantidad_disponible >= 0", name="ck_stock_disponible"),
        sa.CheckConstraint("cantidad_reservada >= 0", name="ck_stock_reservada"),
    )

    # --- Create movimientos_stock ---
    op.create_table(
        "movimientos_stock",
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
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("cantidad", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "pedido_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pedidos.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "tipo IN ('reserva', 'confirmacion', 'devolucion', 'ajuste')",
            name="ck_mov_stock_tipo",
        ),
        sa.CheckConstraint("cantidad > 0", name="ck_mov_stock_cantidad"),
    )
    op.create_index("idx_mov_stock_product_id", "movimientos_stock", ["product_id"])
    op.create_index("idx_mov_stock_pedido_id", "movimientos_stock", ["pedido_id"])
    op.create_index("idx_mov_stock_created_at", "movimientos_stock", [sa.text("created_at DESC")])
    op.create_index("idx_mov_stock_product_tipo", "movimientos_stock", ["product_id", "tipo"])

    # --- Create facturas ---
    op.create_table(
        "facturas",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "orden_compra_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ordenes_compra.id", ondelete="RESTRICT"),
            unique=True,
            nullable=False,
        ),
        sa.Column("numero_fiscal", sa.String(length=30), unique=True, nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("total >= 0", name="ck_facturas_total"),
        sa.UniqueConstraint("orden_compra_id", name="uq_facturas_orden_compra_id"),
        sa.UniqueConstraint("numero_fiscal", name="uq_facturas_numero_fiscal"),
    )
    op.create_index("idx_facturas_created_at", "facturas", ["created_at"])
    op.create_index("idx_facturas_created_by", "facturas", ["created_by"])
    op.create_index("idx_facturas_numero_fiscal", "facturas", ["numero_fiscal"], unique=True)
    op.create_index("idx_facturas_orden_compra_id", "facturas", ["orden_compra_id"], unique=True)

    # --- Seed stock rows for existing productos ---
    op.execute(sa.text("INSERT INTO stock (product_id, cantidad_disponible, cantidad_reservada) SELECT id, 0, 0 FROM productos ON CONFLICT (product_id) DO NOTHING") if not is_sqlite else sa.text("INSERT OR IGNORE INTO stock (product_id, cantidad_disponible, cantidad_reservada) SELECT id, 0, 0 FROM productos"))

    # --- Trigger for stock updated_at ---
    if not is_sqlite:
        op.execute(
            sa.text(
                """
            CREATE TRIGGER trg_stock_updated_at
            BEFORE UPDATE ON stock
            FOR EACH ROW EXECUTE FUNCTION update_updated_at();
            """
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else "postgresql"
    is_sqlite = dialect == "sqlite"

    if not is_sqlite:
        op.execute(sa.text("DROP TRIGGER IF EXISTS trg_stock_updated_at ON stock"))

    op.drop_index("idx_facturas_orden_compra_id", table_name="facturas")
    op.drop_index("idx_facturas_numero_fiscal", table_name="facturas")
    op.drop_index("idx_facturas_created_by", table_name="facturas")
    op.drop_index("idx_facturas_created_at", table_name="facturas")
    op.drop_table("facturas")

    op.drop_index("idx_mov_stock_product_tipo", table_name="movimientos_stock")
    op.drop_index("idx_mov_stock_created_at", table_name="movimientos_stock")
    op.drop_index("idx_mov_stock_pedido_id", table_name="movimientos_stock")
    op.drop_index("idx_mov_stock_product_id", table_name="movimientos_stock")
    op.drop_table("movimientos_stock")

    op.drop_table("stock")

    if not is_sqlite:
        op.execute(sa.text("ALTER TABLE pedidos DROP CONSTRAINT IF EXISTS ck_pedidos_estado"))
        op.execute(
            sa.text(
                "ALTER TABLE pedidos ADD CONSTRAINT ck_pedidos_estado "
                "CHECK (estado IN ('pendiente', 'aceptado', 'rechazado'))"
            )
        )
