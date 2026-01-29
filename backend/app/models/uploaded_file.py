"""
UploadedFile model - Arquivos PDF enviados
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.analysis_job import AnalysisJob
    from app.models.document_extraction import DocumentExtraction


class UploadedFile(Base):
    """Arquivo PDF enviado pelo usuário."""

    __tablename__ = "uploaded_files"

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign Keys
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"), index=True
    )

    # File info
    original_filename: Mapped[str] = mapped_column(Text)
    mime_type: Mapped[str] = mapped_column(String, default="application/pdf")
    file_size: Mapped[int] = mapped_column(BigInteger)
    file_sha256: Mapped[str] = mapped_column(String, index=True)

    # Storage
    storage_url: Mapped[str] = mapped_column(Text)
    storage_provider: Mapped[str] = mapped_column(String, default="minio")

    # Metadata
    file_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)

    # Relationships
    job: Mapped["AnalysisJob"] = relationship("AnalysisJob", back_populates="uploaded_files")

    extractions: Mapped[list["DocumentExtraction"]] = relationship(
        "DocumentExtraction", back_populates="file", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UploadedFile(id={self.id}, filename={self.original_filename})>"

    @property
    def size_mb(self) -> float:
        """Retorna o tamanho do arquivo em MB."""
        return self.file_size / (1024 * 1024)
