"""Add products and offers

Revision ID: 20260203_products_offers
Revises: 20260202_divida_total_red
Create Date: 2026-02-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260203_products_offers"
down_revision: Union[str, None] = "20260202_divida_total_red"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("base_value_cent", sa.BigInteger(), nullable=False),
        sa.Column("installments", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("payment_methods", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_products_name", "products", ["name"])

    op.add_column(
        "analysis_jobs",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_analysis_jobs_product_id", "analysis_jobs", ["product_id"])
    op.create_foreign_key(
        "analysis_jobs_product_id_fkey",
        "analysis_jobs",
        "products",
        ["product_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.create_table(
        "offers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("installment_count", sa.Integer(), nullable=False),
        sa.Column("installment_value_cent", sa.BigInteger(), nullable=False),
        sa.Column("total_value_cent", sa.BigInteger(), nullable=False),
        sa.Column("first_payment_days", sa.Integer(), nullable=False),
        sa.Column("payment_method", sa.String(length=20), nullable=False),
        sa.Column("salary_liquid_used_cent", sa.BigInteger(), nullable=False),
        sa.Column("percent_used", sa.Integer(), nullable=False),
        sa.Column("seed", sa.String(length=120), nullable=False),
        sa.Column("text", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("kind IN ('PRINCIPAL', 'REDUZIDA', 'SUPER')", name="offer_kind_values"),
        sa.CheckConstraint("payment_method IN ('PIX', 'BOLETO')", name="offer_payment_method_values"),
    )
    op.create_index("ix_offers_job_id", "offers", ["job_id"])
    op.create_index("ix_offers_product_id", "offers", ["product_id"])
    op.create_foreign_key(
        "offers_job_id_fkey",
        "offers",
        "analysis_jobs",
        ["job_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "offers_product_id_fkey",
        "offers",
        "products",
        ["product_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("offers_product_id_fkey", "offers", type_="foreignkey")
    op.drop_constraint("offers_job_id_fkey", "offers", type_="foreignkey")
    op.drop_index("ix_offers_product_id", table_name="offers")
    op.drop_index("ix_offers_job_id", table_name="offers")
    op.drop_table("offers")

    op.drop_constraint(
        "analysis_jobs_product_id_fkey", "analysis_jobs", type_="foreignkey"
    )
    op.drop_index("ix_analysis_jobs_product_id", table_name="analysis_jobs")
    op.drop_column("analysis_jobs", "product_id")

    op.drop_index("ix_products_name", table_name="products")
    op.drop_table("products")
