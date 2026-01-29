"""
AnalysisJob schemas - Pydantic models for Job API validation
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AnalysisJobCreate(BaseModel):
    """
    Schema para criação de job de análise.
    Valores declarados são opcionais e em formato moeda (ex: "2500.00").
    """

    renda_mensal_declarada: str | None = Field(
        None,
        description="Renda mensal declarada em formato BRL",
        examples=["2500.00", "1234.56"],
    )
    gasto_dividas_declarado: str | None = Field(
        None,
        description="Gasto mensal com dívidas declarado em formato BRL",
        examples=["800.00", "123.45"],
    )

    @field_validator("renda_mensal_declarada", "gasto_dividas_declarado")
    @classmethod
    def validate_monetary_value(cls, v: str | None) -> str | None:
        """Valida formato de valor monetário."""
        if v is None:
            return v

        # Remove espaços e R$
        v = v.strip().replace("R$", "").replace(" ", "")

        # Normalizar formato brasileiro: remover pontos (milhares) e converter vírgula (decimal)
        v = v.replace(".", "")  # Remove separador de milhares
        v = v.replace(",", ".")  # Converte vírgula decimal para ponto

        try:
            value = float(v)
            if value < 0:
                raise ValueError("Valor não pode ser negativo")
            if value > 999999.99:
                raise ValueError("Valor máximo excedido (999.999,99)")
            return f"{value:.2f}"
        except ValueError as e:
            raise ValueError(f"Valor monetário inválido: {e}") from e


class AnalysisJobStatus(BaseModel):
    """Schema para status de job."""

    job_id: UUID
    status: str
    progress: dict | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class AnalysisJobResponse(BaseModel):
    """Schema para resposta de job."""

    id: UUID
    status: str
    competencia_alvo: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    error_code: str | None = None
    error_message: str | None = None

    model_config = {"from_attributes": True}
