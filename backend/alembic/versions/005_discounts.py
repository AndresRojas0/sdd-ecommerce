"""Discounts per ADR-008 — offer fields on productos, precio_lista snapshot on pedido_items.

- productos: precio_descuento (NULL = sin oferta) + vigencia desde/hasta,
  with CHECK (NULL or < precio).
- pedido_items: precio_lista added nullable, backfilled from precio_unitario
  (historical snapshots had no discount concept), then set NOT NULL.

Revision ID: 005_discounts
Revises: 004_refresh_token_aud
Create Date: 2026-09-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_discounts"
down_revision: Union[str, None] = "004_refresh_token_aud"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else "postgresql"
    is_sqlite = dialect == "sqlite"

    if is_sqlite:
        with op.batch_alter_table("productos", recreate="auto") as batch_op:
            batch_op.add_column(sa.Column("precio_descuento", sa.Numeric(10, 2), nullable=True))
            batch_op.add_column(sa.Column("descuento_desde", sa.DateTime(timezone=True), nullable=True))
            batch_op.add_column(sa.Column("descuento_hasta", sa.DateTime(timezone=True), nullable=True))
            batch_op.create_check_constraint(
                "ck_productos_precio_descuento",
                "precio_descuento IS NULL OR precio_descuento < precio",
            )
        # precio_lista: add nullable -> backfill -> NOT NULL (single migration)
        with op.batch_alter_table("pedido_items", recreate="auto") as batch_op:
            batch_op.add_column(sa.Column("precio_lista", sa.Numeric(10, 2), nullable=True))
        op.execute(sa.text("UPDATE pedido_items SET precio_lista = precio_unitario"))
        with op.batch_alter_table("pedido_items", recreate="auto") as batch_op:
            batch_op.alter_column("precio_lista", existing_type=sa.Numeric(10, 2), nullable=False)
            batch_op.create_check_constraint(
                "ck_pedido_items_precio_lista",
                "precio_lista > 0",
            )
    else:
        op.add_column("productos", sa.Column("precio_descuento", sa.Numeric(10, 2), nullable=True))
        op.add_column("productos", sa.Column("descuento_desde", sa.DateTime(timezone=True), nullable=True))
        op.add_column("productos", sa.Column("descuento_hasta", sa.DateTime(timezone=True), nullable=True))
        op.create_check_constraint(
            "ck_productos_precio_descuento",
            "productos",
            "precio_descuento IS NULL OR precio_descuento < precio",
        )
        op.add_column("pedido_items", sa.Column("precio_lista", sa.Numeric(10, 2), nullable=True))
        op.execute(sa.text("UPDATE pedido_items SET precio_lista = precio_unitario"))
        op.alter_column("pedido_items", "precio_lista", existing_type=sa.Numeric(10, 2), nullable=False)
        op.create_check_constraint(
            "ck_pedido_items_precio_lista",
            "pedido_items",
            "precio_lista > 0",
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else "postgresql"
    is_sqlite = dialect == "sqlite"

    if is_sqlite:
        with op.batch_alter_table("pedido_items", recreate="auto") as batch_op:
            batch_op.drop_column("precio_lista")
        with op.batch_alter_table("productos", recreate="auto") as batch_op:
            batch_op.drop_constraint("ck_productos_precio_descuento", type_="check")
            batch_op.drop_column("precio_descuento")
            batch_op.drop_column("descuento_desde")
            batch_op.drop_column("descuento_hasta")
    else:
        op.drop_constraint("ck_pedido_items_precio_lista", "pedido_items", type_="check")
        op.drop_column("pedido_items", "precio_lista")
        op.drop_constraint("ck_productos_precio_descuento", "productos", type_="check")
        op.drop_column("productos", "descuento_hasta")
        op.drop_column("productos", "descuento_desde")
        op.drop_column("productos", "precio_descuento")
