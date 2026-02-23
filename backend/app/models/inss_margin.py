"""
INSSMargin model - Dados de margem do extrato consignado INSS
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


class INSSMargin(Base):
    """Dados de margem extraídos do extrato INSS."""

    __tablename__ = "inss_margins"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"), unique=True, index=True
    )
    source_file_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uploaded_files.id", ondelete="SET NULL")
    )

    base_calculo_cent: Mapped[int | None] = mapped_column(BigInteger)
    max_comprometimento_cent: Mapped[int | None] = mapped_column(BigInteger)
    total_comprometido_cent: Mapped[int | None] = mapped_column(BigInteger)
    margem_emprestimo_cent: Mapped[int | None] = mapped_column(BigInteger)
    margem_rmc_cent: Mapped[int | None] = mapped_column(BigInteger)
    margem_rcc_cent: Mapped[int | None] = mapped_column(BigInteger)
    cet_mensal: Mapped[str | None] = mapped_column(String(20))
    cet_anual: Mapped[str | None] = mapped_column(String(20))

    # RF-011
    rmc_banco: Mapped[str | None] = mapped_column(String(120))
    rmc_limite_cent: Mapped[int | None] = mapped_column(BigInteger)
    rmc_reservado_cent: Mapped[int | None] = mapped_column(BigInteger)

    evidence: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    job: Mapped["AnalysisJob"] = relationship("AnalysisJob", back_populates="inss_margin")
    source_file: Mapped["UploadedFile | None"] = relationship("UploadedFile")

    def __repr__(self) -> str:
        return f"<INSSMargin(job_id={self.job_id})>"
