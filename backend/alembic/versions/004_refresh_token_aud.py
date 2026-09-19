"""Add aud to refresh_tokens (ADR-003/005 audience separation).

Existing rows belong to the store audience (the only surface that existed
before this revision), so they are backfilled with 'store' via server_default.

Revision ID: 004_refresh_token_aud
Revises: 003_categories_tree_collections
Create Date: 2026-09-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_refresh_token_aud"
down_revision: Union[str, None] = "003_categories_tree_collections"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else "postgresql"
    is_sqlite = dialect == "sqlite"

    if is_sqlite:
        with op.batch_alter_table("refresh_tokens", recreate="auto") as batch_op:
            batch_op.add_column(
                sa.Column("aud", sa.String(length=10), nullable=False, server_default=sa.text("'store'"))
            )
    else:
        op.add_column(
            "refresh_tokens",
            sa.Column("aud", sa.String(length=10), nullable=False, server_default=sa.text("'store'")),
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else "postgresql"
    is_sqlite = dialect == "sqlite"

    if is_sqlite:
        with op.batch_alter_table("refresh_tokens", recreate="auto") as batch_op:
            batch_op.drop_column("aud")
    else:
        op.drop_column("refresh_tokens", "aud")
