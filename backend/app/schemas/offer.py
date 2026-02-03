"""
Offer schemas - Pydantic models for offers
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class OfferResponse(BaseModel):
    id: UUID
    product_id: UUID
    kind: str
    installment_count: int
    installment_value_cent: int
    total_value_cent: int
    entry_value_cent: int | None = None
    entry_due_days: int | None = None
    first_payment_days: int
    payment_method: str
    salary_liquid_used_cent: int
    percent_used: int
    text: str
    created_at: datetime

    model_config = {"from_attributes": True}
