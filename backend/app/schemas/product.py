"""
Product schemas - Pydantic models for product API
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

ALLOWED_PAYMENT_METHODS = {"PIX", "BOLETO"}
INSTALLMENT_MIN = 6
INSTALLMENT_MAX = 24


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    base_value_cent: int = Field(..., gt=0, description="Valor do produto em centavos")
    installments: list[int] = Field(..., min_length=1)
    payment_methods: list[str] = Field(..., min_length=1)

    @field_validator("installments")
    @classmethod
    def validate_installments(cls, v: list[int]) -> list[int]:
        unique = sorted({int(x) for x in v})
        if not unique:
            raise ValueError("Parcelamentos não pode ser vazio")
        for value in unique:
            if value < INSTALLMENT_MIN or value > INSTALLMENT_MAX:
                raise ValueError(
                    f"Parcelamentos devem estar entre {INSTALLMENT_MIN} e {INSTALLMENT_MAX}"
                )
        return unique

    @field_validator("payment_methods")
    @classmethod
    def validate_payment_methods(cls, v: list[str]) -> list[str]:
        normalized = [item.strip().upper() for item in v if item]
        if not normalized:
            raise ValueError("Formas de pagamento não pode ser vazio")
        invalid = [item for item in normalized if item not in ALLOWED_PAYMENT_METHODS]
        if invalid:
            raise ValueError(
                f"Formas de pagamento inválidas: {', '.join(invalid)}"
            )
        return sorted(set(normalized))


class ProductResponse(BaseModel):
    id: UUID
    name: str
    base_value_cent: int
    installments: list[int]
    payment_methods: list[str]
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
