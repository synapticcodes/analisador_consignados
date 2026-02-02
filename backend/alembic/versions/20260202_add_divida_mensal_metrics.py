"""Add divida mensal metrics

Revision ID: 20260202_divida_mensal
Revises: None
Create Date: 2026-02-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260202_divida_mensal"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "final_results",
        sa.Column("divida_mensal_cent", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "final_results",
        sa.Column("divida_mensal_reduzida_cent", sa.BigInteger(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("final_results", "divida_mensal_reduzida_cent")
    op.drop_column("final_results", "divida_mensal_cent")
