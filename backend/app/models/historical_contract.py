"""
HistoricalContract model - Contratos encerrados/históricos do extrato INSS
"""

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Date, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.analysis_job import AnalysisJob
    from app.models.uploaded_file import UploadedFile


class HistoricalContract(Base):
    """Contrato histórico extraído da seção de encerrados/excluídos do INSS."""

    __tablename__ = "historical_contracts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"), index=True
    )
    source_file_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uploaded_files.id", ondelete="SET NULL")
    )

    lender_name: Mapped[str | None] = mapped_column(String(255))
    contract_id: Mapped[str | None] = mapped_column(String(120))
    data_contratacao: Mapped[date | None] = mapped_column(Date)
    data_quitacao: Mapped[date | None] = mapped_column(Date)
    parcela_cent: Mapped[int | None] = mapped_column(BigInteger)
    valor_emprestado_cent: Mapped[int | None] = mapped_column(BigInteger)
    motivo_encerramento: Mapped[str | None] = mapped_column(String(120))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    job: Mapped["AnalysisJob"] = relationship(
        "AnalysisJob", back_populates="historical_contracts"
    )
    source_file: Mapped["UploadedFile | None"] = relationship("UploadedFile")

    def __repr__(self) -> str:
        return f"<HistoricalContract(job_id={self.job_id}, contract_id={self.contract_id})>"
