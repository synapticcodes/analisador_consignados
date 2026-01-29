"""
AnalysisJob model - Jobs de análise de PDFs
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
    from app.models.final_result import FinalResult
    from app.models.loan_contract import LoanContract
    from app.models.payroll_month import PayrollMonth
    from app.models.uploaded_file import UploadedFile
    from app.models.user import User


class JobStatus(str, Enum):
    """Status possíveis de um job."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class AnalysisJob(Base):
    """Job de análise de PDFs."""

    __tablename__ = "analysis_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED')",
            name="status_values",
        ),
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign Keys
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    # Status
    status: Mapped[str] = mapped_column(String, default=JobStatus.PENDING.value, index=True)

    # Valores declarados pelo usuário (em centavos)
    renda_mensal_declarada_cent: Mapped[int | None] = mapped_column(BigInteger)
    gasto_dividas_declarado_cent: Mapped[int | None] = mapped_column(BigInteger)

    # Competência consolidada
    competencia_alvo: Mapped[str | None] = mapped_column(String(7))  # YYYY-MM

    # Error tracking
    error_code: Mapped[str | None] = mapped_column(String)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Metadata
    processing_time_ms: Mapped[int | None] = mapped_column(Integer)
    job_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column()

    # Relationships
    user: Mapped["User | None"] = relationship("User", back_populates="jobs")

    uploaded_files: Mapped[list["UploadedFile"]] = relationship(
        "UploadedFile", back_populates="job", cascade="all, delete-orphan"
    )

    loan_contracts: Mapped[list["LoanContract"]] = relationship(
        "LoanContract", back_populates="job", cascade="all, delete-orphan"
    )

    payroll_months: Mapped[list["PayrollMonth"]] = relationship(
        "PayrollMonth", back_populates="job", cascade="all, delete-orphan"
    )

    final_result: Mapped["FinalResult | None"] = relationship(
        "FinalResult", back_populates="job", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AnalysisJob(id={self.id}, status={self.status})>"

    @property
    def is_completed(self) -> bool:
        """Verifica se o job foi completado (sucesso ou falha)."""
        return self.status in (JobStatus.SUCCEEDED.value, JobStatus.FAILED.value)

    @property
    def is_successful(self) -> bool:
        """Verifica se o job foi completado com sucesso."""
        return self.status == JobStatus.SUCCEEDED.value

    def to_dict(self) -> dict:
        """Converte para dicionário (útil para serialização)."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "status": self.status,
            "competencia_alvo": self.competencia_alvo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
