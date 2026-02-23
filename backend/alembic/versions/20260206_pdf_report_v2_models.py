"""Add models for relatorio PDF v2

Revision ID: 20260206_pdf_report_v2
Revises: 20260203_offers_entry
Create Date: 2026-02-06 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260206_pdf_report_v2"
down_revision: Union[str, None] = "20260203_offers_entry"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "loan_contracts",
        sa.Column("taxa_juros", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "loan_contracts",
        sa.Column("cet_mensal", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "loan_contracts",
        sa.Column("cet_anual", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "loan_contracts",
        sa.Column("iof_cent", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "loan_contracts",
        sa.Column("valor_emprestado_cent", sa.BigInteger(), nullable=True),
    )

    op.create_table(
        "inss_margins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("base_calculo_cent", sa.BigInteger(), nullable=True),
        sa.Column("max_comprometimento_cent", sa.BigInteger(), nullable=True),
        sa.Column("total_comprometido_cent", sa.BigInteger(), nullable=True),
        sa.Column("margem_emprestimo_cent", sa.BigInteger(), nullable=True),
        sa.Column("margem_rmc_cent", sa.BigInteger(), nullable=True),
        sa.Column("margem_rcc_cent", sa.BigInteger(), nullable=True),
        sa.Column("cet_mensal", sa.String(length=20), nullable=True),
        sa.Column("cet_anual", sa.String(length=20), nullable=True),
        sa.Column("rmc_banco", sa.String(length=120), nullable=True),
        sa.Column("rmc_limite_cent", sa.BigInteger(), nullable=True),
        sa.Column("rmc_reservado_cent", sa.BigInteger(), nullable=True),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["job_id"], ["analysis_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_file_id"], ["uploaded_files.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_inss_margins_job_id", "inss_margins", ["job_id"])

    op.create_table(
        "historical_contracts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lender_name", sa.String(length=255), nullable=True),
        sa.Column("contract_id", sa.String(length=120), nullable=True),
        sa.Column("data_contratacao", sa.Date(), nullable=True),
        sa.Column("data_quitacao", sa.Date(), nullable=True),
        sa.Column("parcela_cent", sa.BigInteger(), nullable=True),
        sa.Column("valor_emprestado_cent", sa.BigInteger(), nullable=True),
        sa.Column("motivo_encerramento", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["job_id"], ["analysis_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_file_id"], ["uploaded_files.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_historical_contracts_job_id", "historical_contracts", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_historical_contracts_job_id", table_name="historical_contracts")
    op.drop_table("historical_contracts")

    op.drop_index("ix_inss_margins_job_id", table_name="inss_margins")
    op.drop_table("inss_margins")

    op.drop_column("loan_contracts", "valor_emprestado_cent")
    op.drop_column("loan_contracts", "iof_cent")
    op.drop_column("loan_contracts", "cet_anual")
    op.drop_column("loan_contracts", "cet_mensal")
    op.drop_column("loan_contracts", "taxa_juros")
