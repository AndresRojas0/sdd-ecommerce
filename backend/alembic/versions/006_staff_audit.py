"""Staff audit table — auditoría de staff append-only (02-security.md, A-AUD-01).

Tabla inmutable: la aplicación solo INSERTA filas (nunca UPDATE/DELETE).
Revision ID: 006_staff_audit
Revises: 005_discounts
Create Date: 2026-09-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "006_staff_audit"
down_revision: Union[str, None] = "005_discounts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else "postgresql"
    is_sqlite = dialect == "sqlite"

    if is_sqlite:
        op.create_table(
            "staff_audits",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("accion", sa.String(100), nullable=False),
            sa.Column("entidad", sa.String(50), nullable=False),
            sa.Column("entidad_id", sa.String(64), nullable=True),
            sa.Column("datos_antes", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("datos_despues", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("request_id", sa.String(64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
    else:
        op.create_table(
            "staff_audits",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column(
                "actor_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("accion", sa.String(100), nullable=False),
            sa.Column("entidad", sa.String(50), nullable=False),
            sa.Column("entidad_id", sa.String(64), nullable=True),
            sa.Column("datos_antes", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("datos_despues", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("request_id", sa.String(64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )

    op.create_index("idx_staff_audits_entidad", "staff_audits", ["entidad", "entidad_id"])
    op.create_index("idx_staff_audits_actor", "staff_audits", ["actor_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_staff_audits_actor", table_name="staff_audits")
    op.drop_index("idx_staff_audits_entidad", table_name="staff_audits")
    op.drop_table("staff_audits")
