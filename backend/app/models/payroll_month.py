"""
PayrollMonth model - Dados de folha de pagamento por competência
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.analysis_job import AnalysisJob
    from app.models.uploaded_file import UploadedFile


class PayrollMonth(Base):
    """Dados consolidados de folha de pagamento para uma competência específica."""

    __tablename__ = "payroll_months"

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign Keys
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"), index=True
    )
    source_file_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uploaded_files.id", ondelete="SET NULL")
    )

    # Competência (YYYY-MM)
    competencia: Mapped[str] = mapped_column(String(7), index=True)

    # Valores consolidados (em centavos)
    bruto_cent: Mapped[int | None] = mapped_column(BigInteger)
    liquido_cent: Mapped[int | None] = mapped_column(BigInteger)
    descontos_cent: Mapped[int | None] = mapped_column(BigInteger)
    consignado_cent: Mapped[int | None] = mapped_column(BigInteger)

    # Métodos utilizados para obter cada valor
    method_bruto: Mapped[str | None] = mapped_column(String)
    method_liquido: Mapped[str | None] = mapped_column(String)
    method_descontos: Mapped[str | None] = mapped_column(String)
    method_consignado: Mapped[str | None] = mapped_column(String)

    # Evidence & provenance
    evidence: Mapped[dict | None] = mapped_column(JSONB)
    provenance: Mapped[dict | None] = mapped_column(JSONB)

    # Linhas de consignado individuais (array de objetos)
    consignado_lines: Mapped[list | None] = mapped_column(JSONB)

    # Alertas
    alerts: Mapped[list | None] = mapped_column(JSONB)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    job: Mapped["AnalysisJob"] = relationship("AnalysisJob", back_populates="payroll_months")

    source_file: Mapped["UploadedFile | None"] = relationship("UploadedFile")

    def __repr__(self) -> str:
        return f"<PayrollMonth(id={self.id}, competencia={self.competencia})>"

    @property
    def bruto_brl(self) -> float:
        """Retorna salário bruto em reais."""
        return self.bruto_cent / 100 if self.bruto_cent else 0.0

    @property
    def liquido_brl(self) -> float:
        """Retorna salário líquido em reais."""
        return self.liquido_cent / 100 if self.liquido_cent else 0.0

    @property
    def descontos_brl(self) -> float:
        """Retorna total de descontos em reais."""
        return self.descontos_cent / 100 if self.descontos_cent else 0.0

    @property
    def consignado_brl(self) -> float:
        """Retorna consignado mensal em reais."""
        return self.consignado_cent / 100 if self.consignado_cent else 0.0

    def validate_invariants(self) -> list[str]:
        """
        Valida invariantes matemáticos.
        Retorna lista de erros encontrados.
        """
        errors = []

        # Bruto >= Líquido
        if self.bruto_cent and self.liquido_cent:
            if self.bruto_cent < self.liquido_cent:
                errors.append("Salário bruto não pode ser menor que líquido")

        # Descontos >= 0
        if self.descontos_cent and self.descontos_cent < 0:
            errors.append("Descontos não podem ser negativos")

        # Consignado >= 0
        if self.consignado_cent and self.consignado_cent < 0:
            errors.append("Consignado não pode ser negativo")

        # Bruto - Líquido ≈ Descontos (com tolerância de 1 centavo)
        if self.bruto_cent and self.liquido_cent and self.descontos_cent:
            calculated_descontos = self.bruto_cent - self.liquido_cent
            diff = abs(calculated_descontos - self.descontos_cent)
            if diff > 1:  # Tolerância de 1 centavo
                errors.append(
                    f"Inconsistência: Bruto - Líquido ({calculated_descontos}) "
                    f"!= Descontos ({self.descontos_cent})"
                )

        return errors
