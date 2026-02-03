"""
Product model - Catálogo de produtos para geração de ofertas
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Boolean, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.analysis_job import AnalysisJob
    from app.models.offer import Offer


class Product(Base):
    """Produto disponível para geração de ofertas."""

    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    base_value_cent: Mapped[int] = mapped_column(BigInteger, nullable=False)
    installments: Mapped[list[int]] = mapped_column(JSONB, nullable=False)
    payment_methods: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    jobs: Mapped[list["AnalysisJob"]] = relationship(
        "AnalysisJob", back_populates="product"
    )
    offers: Mapped[list["Offer"]] = relationship(
        "Offer", back_populates="product"
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name={self.name})>"
