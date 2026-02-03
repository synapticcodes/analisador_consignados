"""Add entry fields to offers

Revision ID: 20260203_offers_entry
Revises: 20260203_products_offers
Create Date: 2026-02-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260203_offers_entry"
down_revision: Union[str, None] = "20260203_products_offers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "offers",
        sa.Column("entry_value_cent", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "offers",
        sa.Column("entry_due_days", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("offers", "entry_due_days")
    op.drop_column("offers", "entry_value_cent")
