"""
LoanContract model - Contratos de empréstimo consignado extraídos
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.analysis_job import AnalysisJob
    from app.models.uploaded_file import UploadedFile


class ContractStatus(str, Enum):
    """Status de um contrato de empréstimo."""

    ATIVO = "ATIVO"
    QUITADO = "QUITADO"
    INDEFINIDO = "INDEFINIDO"


class LoanContract(Base):
    """Contrato de empréstimo consignado extraído."""

    __tablename__ = "loan_contracts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ATIVO', 'QUITADO', 'INDEFINIDO')",
            name="status_values",
        ),
        # Unique constraint para evitar duplicatas
        {"schema": None},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign Keys
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"), index=True
    )
    source_file_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uploaded_files.id", ondelete="SET NULL")
    )

    # Contract info
    lender_name: Mapped[str | None] = mapped_column(Text)
    contract_id: Mapped[str | None] = mapped_column(String)
    contract_key: Mapped[str] = mapped_column(String, index=True)  # Hash for dedup

    # Valores (em centavos)
    parcela_cent: Mapped[int | None] = mapped_column(BigInteger)
    total_parcelas: Mapped[int | None] = mapped_column(Integer)
    parcelas_pagas: Mapped[int | None] = mapped_column(Integer)
    parcelas_restantes: Mapped[int | None] = mapped_column(Integer)
    valor_total_cent: Mapped[int | None] = mapped_column(BigInteger)
    iof_cent: Mapped[int | None] = mapped_column(BigInteger)
    valor_emprestado_cent: Mapped[int | None] = mapped_column(BigInteger)

    # Status
    status: Mapped[str] = mapped_column(String, default=ContractStatus.ATIVO.value)
    taxa_juros: Mapped[str | None] = mapped_column(String(20))
    cet_mensal: Mapped[str | None] = mapped_column(String(20))
    cet_anual: Mapped[str | None] = mapped_column(String(20))

    # Evidence
    evidence: Mapped[dict | None] = mapped_column(JSONB)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    job: Mapped["AnalysisJob"] = relationship("AnalysisJob", back_populates="loan_contracts")

    source_file: Mapped["UploadedFile | None"] = relationship("UploadedFile")

    def __repr__(self) -> str:
        return f"<LoanContract(id={self.id}, lender={self.lender_name}, status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Verifica se o contrato está ativo."""
        return self.status == ContractStatus.ATIVO.value

    @property
    def parcela_brl(self) -> float:
        """Retorna valor da parcela em reais."""
        return self.parcela_cent / 100 if self.parcela_cent else 0.0

    @property
    def valor_total_brl(self) -> float:
        """Retorna valor total em reais."""
        return self.valor_total_cent / 100 if self.valor_total_cent else 0.0

    def calculate_missing_fields(self) -> None:
        """
        Calcula campos faltantes quando possível.
        - valor_total = parcela * total_parcelas
        - parcelas_restantes = total_parcelas - parcelas_pagas
        """
        # Calcular valor total se ausente
        if (
            self.valor_total_cent is None
            and self.parcela_cent is not None
            and self.total_parcelas is not None
        ):
            self.valor_total_cent = self.parcela_cent * self.total_parcelas

        # Calcular parcelas restantes se ausente
        if (
            self.parcelas_restantes is None
            and self.total_parcelas is not None
            and self.parcelas_pagas is not None
        ):
            self.parcelas_restantes = self.total_parcelas - self.parcelas_pagas
