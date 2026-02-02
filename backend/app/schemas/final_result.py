"""
FinalResult schemas - Pydantic models para os 9 outputs finais
"""

from uuid import UUID

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """Evidência de um valor extraído."""

    file_id: UUID
    page: int
    text: str


class MonetaryField(BaseModel):
    """
    Campo monetário com valor, moeda, fonte e evidência.
    Formato padrão para os 8 outputs principais.
    """

    value: float | None = Field(None, description="Valor em reais (BRL)")
    currency: str = Field("BRL", description="Moeda")
    source: str | None = Field(None, description="Tipo de documento fonte")
    evidence: Evidence | None = Field(None, description="Evidência do valor")
    method: str | None = Field(None, description="Método usado para obter/calcular")


class FinalResultResponse(BaseModel):
    """
    Response com os 9 outputs finais consolidados.
    Este é o schema principal que a API retorna.
    """

    job_id: UUID
    competencia_alvo: str = Field(
        ..., description="Competência (mês/ano) dos dados", examples=["2026-01"]
    )

    # Os 9 outputs principais
    salario_bruto: MonetaryField = Field(..., description="Salário bruto mensal")
    salario_liquido: MonetaryField = Field(..., description="Salário líquido mensal")
    total_descontos: MonetaryField = Field(..., description="Total de descontos mensais")
    divida_mensal: MonetaryField = Field(..., description="Dívida mensal (90% dos descontos)")
    divida_mensal_reduzida: MonetaryField = Field(
        ..., description="Dívida mensal reduzida (25% da dívida mensal)"
    )
    consignado_mensal: MonetaryField = Field(
        ..., description="Valor mensal de consignados"
    )
    divida_total_consignada: MonetaryField = Field(
        ..., description="Dívida total de empréstimos consignados"
    )
    divida_total_reduzida: MonetaryField = Field(
        ..., description="Dívida total reduzida (25% da dívida total consignada)"
    )
    parcelas_restantes_total: int | None = Field(
        None, description="Total de parcelas restantes de todos os contratos"
    )

    # Alertas e metadata
    alerts: list[str] = Field(default_factory=list, description="Alertas de inconsistências")

    model_config = {"from_attributes": True}


class FinalResultSummary(BaseModel):
    """Resumo simplificado do resultado (sem evidências)."""

    job_id: UUID
    competencia_alvo: str
    salario_bruto: float | None
    salario_liquido: float | None
    total_descontos: float | None
    divida_mensal: float | None
    divida_mensal_reduzida: float | None
    consignado_mensal: float | None
    divida_total: float | None
    divida_total_reduzida: float | None
    parcelas_restantes: int | None
