"""
FinalResult schemas - Pydantic models para os outputs do relatório.
"""

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.offer import OfferResponse


class Evidence(BaseModel):
    """Evidência de um valor extraído."""

    file_id: UUID
    page: int
    text: str


class MonetaryField(BaseModel):
    """
    Campo monetário com valor, moeda, fonte e evidência.
    Formato legado mantido por compatibilidade.
    """

    value: float | None = Field(None, description="Valor em reais (BRL)")
    currency: str = Field("BRL", description="Moeda")
    source: str | None = Field(None, description="Tipo de documento fonte")
    evidence: Evidence | None = Field(None, description="Evidência do valor")
    method: str | None = Field(None, description="Método usado para obter/calcular")


class LoanContractDetail(BaseModel):
    id: UUID
    lender_name: str
    contract_id: str | None = None
    parcela_cent: int | None = None
    parcelas_restantes: int | None = None
    valor_total_cent: int | None = None
    taxa_juros: str | None = None
    status: str = "ATIVO"
    cet_mensal: str | None = None
    cet_anual: str | None = None
    iof_cent: int | None = None
    valor_emprestado_cent: int | None = None


class ConsignadoLineDetail(BaseModel):
    descricao: str
    descricao_raw: str | None = None
    descricao_canonica: str | None = None
    rubrica: str | None = None
    valor_cent: int


class INSSMarginDetail(BaseModel):
    base_calculo_cent: int | None = None
    max_comprometimento_cent: int | None = None
    total_comprometido_cent: int | None = None
    margem_emprestimo_cent: int | None = None
    margem_rmc_cent: int | None = None
    margem_rcc_cent: int | None = None
    cet_mensal: str | None = None
    cet_anual: str | None = None
    rmc_banco: str | None = None
    rmc_limite_cent: int | None = None
    rmc_reservado_cent: int | None = None
    evidence: dict | None = None


class HistoricalContractDetail(BaseModel):
    id: UUID
    lender_name: str | None = None
    contract_id: str | None = None
    data_contratacao: str | None = None
    data_quitacao: str | None = None
    parcela_cent: int | None = None
    valor_emprestado_cent: int | None = None
    motivo_encerramento: str | None = None


class ContractCostDetail(BaseModel):
    contract_id: str | None = None
    lender_name: str | None = None
    parcela_cent: int | None = None
    parcelas_restantes: int | None = None
    valor_emprestado_cent: int | None = None
    total_a_pagar_cent: int | None = None
    custo_juros_cent: int | None = None
    percentual_juros_basis_points: int | None = None


class SavingsSimulationContractDetail(BaseModel):
    contract_key: str
    lender_name: str
    parcela_atual_cent: int
    parcela_nova_estimada_cent: int
    economia_mensal_cent: int
    economia_total_restante_cent: int
    parcelas_restantes: int
    taxa_atual_mensal_percent: str
    taxa_referencia_mensal_percent: str


class SavingsSimulationDetail(BaseModel):
    economia_mensal_total_cent: int
    economia_total_restante_cent: int
    taxa_referencia_mensal_percent: str
    disclaimer: str
    contratos: list[SavingsSimulationContractDetail] = Field(default_factory=list)


class ReportLayers(BaseModel):
    confirmado: list[str] = Field(default_factory=list)
    indicacao: list[str] = Field(default_factory=list)
    nao_disponivel: list[str] = Field(default_factory=list)


class FinalResultResponse(BaseModel):
    """
    Response com os outputs consolidados.
    Mantém campos legados e adiciona blocos v2 de forma aditiva.
    """

    job_id: UUID
    competencia_alvo: str = Field(
        ..., description="Competência (mês/ano) dos dados", examples=["2026-01"]
    )

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

    alerts: list[str] = Field(default_factory=list, description="Alertas de inconsistências")
    offers: list[OfferResponse] = Field(default_factory=list)

    # Campos v2 (aditivos)
    loan_contracts: list[LoanContractDetail] = Field(default_factory=list)
    consignado_lines: list[ConsignadoLineDetail] = Field(default_factory=list)
    inss_margin: INSSMarginDetail | None = None
    historical_contracts: list[HistoricalContractDetail] = Field(default_factory=list)
    custo_juros_total_cent: int | None = None
    custo_juros_total_brl: float | None = None
    custo_juros_por_contrato: list[ContractCostDetail] = Field(default_factory=list)
    savings_simulation: SavingsSimulationDetail | None = None
    report_layers: ReportLayers = Field(default_factory=ReportLayers)

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
