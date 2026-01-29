"""
DocumentExtraction model - Extrações de dados dos documentos via LLM
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.uploaded_file import UploadedFile


class GateStatus(str, Enum):
    """Status da validação do Evidence Gate."""

    PASSED = "PASSED"
    WARN = "WARN"
    FAILED = "FAILED"


class DocumentExtraction(Base):
    """Extração de dados de um documento via LLM."""

    __tablename__ = "document_extractions"
    __table_args__ = (
        CheckConstraint(
            "gate_status IN ('PASSED', 'WARN', 'FAILED')",
            name="gate_status_values",
        ),
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign Keys
    file_id: Mapped[UUID] = mapped_column(
        ForeignKey("uploaded_files.id", ondelete="CASCADE"), index=True
    )

    # Versioning
    extractor_version: Mapped[str] = mapped_column(String, default="1.0")

    # Router output
    router_family: Mapped[str | None] = mapped_column(String, index=True)
    router_confidence: Mapped[float | None] = mapped_column(Float)
    capabilities: Mapped[dict | None] = mapped_column(JSONB)
    competencias_detectadas: Mapped[list | None] = mapped_column(JSONB)

    # Text extraction
    text_quality_score: Mapped[float | None] = mapped_column(Float)
    used_ocr: Mapped[bool] = mapped_column(Boolean, default=False)
    extraction_method: Mapped[str | None] = mapped_column(String)  # 'native', 'ocr'

    # Extractor output
    extracted_json: Mapped[dict | None] = mapped_column(JSONB)
    evidence_json: Mapped[dict | None] = mapped_column(JSONB)

    # Evidence Gate
    gate_status: Mapped[str | None] = mapped_column(String, index=True)
    gate_alerts: Mapped[list | None] = mapped_column(JSONB)

    # Metadata
    processing_time_ms: Mapped[int | None] = mapped_column(Integer)
    extraction_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    file: Mapped["UploadedFile"] = relationship("UploadedFile", back_populates="extractions")

    def __repr__(self) -> str:
        return f"<DocumentExtraction(id={self.id}, family={self.router_family}, gate={self.gate_status})>"

    @property
    def passed_validation(self) -> bool:
        """Verifica se passou pela validação do Evidence Gate."""
        return self.gate_status == GateStatus.PASSED.value

    @property
    def has_warnings(self) -> bool:
        """Verifica se tem warnings."""
        return self.gate_status == GateStatus.WARN.value

    @property
    def failed_validation(self) -> bool:
        """Verifica se falhou na validação."""
        return self.gate_status == GateStatus.FAILED.value
