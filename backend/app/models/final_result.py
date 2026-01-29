"""
FinalResult model - Resultados consolidados finais (6 outputs)
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.analysis_job import AnalysisJob


class FinalResult(Base):
    """Resultado final consolidado de um job de análise."""

    __tablename__ = "final_results"

    # Primary Key (FK para job - relação 1:1)
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"), primary_key=True
    )

    # Competência alvo
    competencia_alvo: Mapped[str] = mapped_column(String(7))

    # ==========================================
    # 6 OUTPUTS PRINCIPAIS (em centavos)
    # ==========================================
    salario_bruto_cent: Mapped[int | None] = mapped_column(BigInteger)
    salario_liquido_cent: Mapped[int | None] = mapped_column(BigInteger)
    total_descontos_cent: Mapped[int | None] = mapped_column(BigInteger)
    consignado_mensal_cent: Mapped[int | None] = mapped_column(BigInteger)
    divida_total_consignada_cent: Mapped[int | None] = mapped_column(BigInteger)
    parcelas_restantes_total: Mapped[int | None] = mapped_column(Integer)

    # Provenance (rastreabilidade de cada valor)
    provenance: Mapped[dict | None] = mapped_column(JSONB)

    # Alertas consolidados
    alerts: Mapped[list | None] = mapped_column(JSONB)

    # Metadata
    calculation_methods: Mapped[dict | None] = mapped_column(JSONB)
    confidence_scores: Mapped[dict | None] = mapped_column(JSONB)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    job: Mapped["AnalysisJob"] = relationship(
        "AnalysisJob", back_populates="final_result", single_parent=True
    )

    def __repr__(self) -> str:
        return f"<FinalResult(job_id={self.job_id}, competencia={self.competencia_alvo})>"

    # ==========================================
    # Properties para conversão BRL
    # ==========================================
    @property
    def salario_bruto_brl(self) -> float | None:
        """Retorna salário bruto em reais."""
        return self.salario_bruto_cent / 100 if self.salario_bruto_cent else None

    @property
    def salario_liquido_brl(self) -> float | None:
        """Retorna salário líquido em reais."""
        return self.salario_liquido_cent / 100 if self.salario_liquido_cent else None

    @property
    def total_descontos_brl(self) -> float | None:
        """Retorna total de descontos em reais."""
        return self.total_descontos_cent / 100 if self.total_descontos_cent else None

    @property
    def consignado_mensal_brl(self) -> float | None:
        """Retorna consignado mensal em reais."""
        return self.consignado_mensal_cent / 100 if self.consignado_mensal_cent else None

    @property
    def divida_total_brl(self) -> float | None:
        """Retorna dívida total em reais."""
        return self.divida_total_consignada_cent / 100 if self.divida_total_consignada_cent else None

    def to_dict(self) -> dict:
        """
        Converte para dicionário com valores em BRL.
        Formato adequado para API response.
        """
        return {
            "job_id": str(self.job_id),
            "competencia_alvo": self.competencia_alvo,
            "salario_bruto": {
                "value": self.salario_bruto_brl,
                "currency": "BRL",
                "source": self.provenance.get("salario_bruto", {}).get("source")
                if self.provenance
                else None,
            },
            "salario_liquido": {
                "value": self.salario_liquido_brl,
                "currency": "BRL",
                "source": self.provenance.get("salario_liquido", {}).get("source")
                if self.provenance
                else None,
            },
            "total_descontos": {
                "value": self.total_descontos_brl,
                "currency": "BRL",
                "method": self.calculation_methods.get("total_descontos")
                if self.calculation_methods
                else None,
            },
            "consignado_mensal": {
                "value": self.consignado_mensal_brl,
                "currency": "BRL",
                "method": self.calculation_methods.get("consignado_mensal")
                if self.calculation_methods
                else None,
            },
            "divida_total_consignada": {
                "value": self.divida_total_brl,
                "currency": "BRL",
                "method": self.calculation_methods.get("divida_total")
                if self.calculation_methods
                else None,
            },
            "parcelas_restantes_total": self.parcelas_restantes_total,
            "alerts": self.alerts or [],
        }

    def validate_invariants(self) -> list[str]:
        """
        Valida invariantes matemáticos dos resultados finais.
        Retorna lista de erros encontrados.
        """
        errors = []

        # Bruto >= Líquido
        if self.salario_bruto_cent and self.salario_liquido_cent:
            if self.salario_bruto_cent < self.salario_liquido_cent:
                errors.append("Salário bruto não pode ser menor que líquido")

        # Descontos >= 0
        if self.total_descontos_cent and self.total_descontos_cent < 0:
            errors.append("Total de descontos não pode ser negativo")

        # Consignado mensal >= 0
        if self.consignado_mensal_cent and self.consignado_mensal_cent < 0:
            errors.append("Consignado mensal não pode ser negativo")

        # Dívida total >= 0
        if self.divida_total_consignada_cent and self.divida_total_consignada_cent < 0:
            errors.append("Dívida total não pode ser negativa")

        # Parcelas restantes >= 0
        if self.parcelas_restantes_total and self.parcelas_restantes_total < 0:
            errors.append("Parcelas restantes não pode ser negativo")

        return errors
