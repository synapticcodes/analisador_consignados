"""
Offer model - Ofertas geradas para um job e produto
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.analysis_job import AnalysisJob
    from app.models.product import Product


class OfferKind(str, Enum):
    PRINCIPAL = "PRINCIPAL"
    REDUZIDA = "REDUZIDA"
    SUPER = "SUPER"


class PaymentMethod(str, Enum):
    PIX = "PIX"
    BOLETO = "BOLETO"


class Offer(Base):
    """Oferta gerada para um job de análise."""

    __tablename__ = "offers"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('PRINCIPAL', 'REDUZIDA', 'SUPER')",
            name="offer_kind_values",
        ),
        CheckConstraint(
            "payment_method IN ('PIX', 'BOLETO')",
            name="offer_payment_method_values",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), index=True
    )

    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    installment_count: Mapped[int] = mapped_column(Integer, nullable=False)
    installment_value_cent: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_value_cent: Mapped[int] = mapped_column(BigInteger, nullable=False)
    entry_value_cent: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    entry_due_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    first_payment_days: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
    salary_liquid_used_cent: Mapped[int] = mapped_column(BigInteger, nullable=False)
    percent_used: Mapped[int] = mapped_column(Integer, nullable=False)
    seed: Mapped[str] = mapped_column(String(120), nullable=False)
    text: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    job: Mapped["AnalysisJob"] = relationship(
        "AnalysisJob", back_populates="offers"
    )
    product: Mapped["Product"] = relationship(
        "Product", back_populates="offers"
    )

    def __repr__(self) -> str:
        return f"<Offer(id={self.id}, kind={self.kind}, job_id={self.job_id})>"
