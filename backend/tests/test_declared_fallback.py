import pytest

from app.services.compute_engine import ComputeEngine, ComputeMethod
from app.services.consolidator import ConsolidatorService, DocumentSource
from app.services.extractors import ExtractedField, LoanContractResult, PaymentExtractionResult


def _field(value: float | None) -> ExtractedField:
    return ExtractedField(
        value=value,
        currency="BRL" if value is not None else None,
        method="EXTRACTED" if value is not None else None,
        evidence=None,
    )


def _payment_result(
    bruto: float | None,
    liquido: float | None,
    descontos: float | None,
) -> PaymentExtractionResult:
    return PaymentExtractionResult(
        competencia="2026-01",
        salario_bruto=_field(bruto),
        salario_liquido=_field(liquido),
        total_descontos=_field(descontos),
        linhas_consignado=[],
        alerts=[],
    )


def _loan_result() -> LoanContractResult:
    return LoanContractResult(
        lender_name="Banco",
        contract_id="123",
        parcela_mensal=_field(100.0),
        total_parcelas=10,
        parcelas_pagas=2,
        parcelas_restantes=None,
        valor_total=_field(1000.0),
        taxa_juros=None,
        alerts=[],
    )


@pytest.mark.unit
def test_salario_liquido_calculado_quando_possivel():
    consolidator = ConsolidatorService()
    consolidated = consolidator.consolidate(
        payment_results=[_payment_result(bruto=5000.0, liquido=None, descontos=1000.0)],
        loan_results=[],
        doc_sources={"payment_0": DocumentSource.PAYROLL_SALARY_STATEMENT},
        renda_mensal_declarada_cent=450000,
    )
    compute = ComputeEngine().compute(consolidated)

    assert compute.salario_liquido_cent == 400000
    assert compute.liquido_source == DocumentSource.PAYROLL_SALARY_STATEMENT.value


@pytest.mark.unit
def test_salario_liquido_fallback_declarado_sem_base_calculo():
    consolidator = ConsolidatorService()
    consolidated = consolidator.consolidate(
        payment_results=[_payment_result(bruto=5000.0, liquido=None, descontos=None)],
        loan_results=[],
        doc_sources={"payment_0": DocumentSource.PAYROLL_SALARY_STATEMENT},
        renda_mensal_declarada_cent=450000,
    )
    compute = ComputeEngine().compute(consolidated)

    assert compute.salario_liquido_cent == 450000
    assert compute.liquido_source == DocumentSource.DECLARADO.value


@pytest.mark.unit
def test_total_descontos_calculado_quando_possivel():
    consolidator = ConsolidatorService()
    consolidated = consolidator.consolidate(
        payment_results=[_payment_result(bruto=5000.0, liquido=4000.0, descontos=None)],
        loan_results=[],
        doc_sources={"payment_0": DocumentSource.PAYROLL_SALARY_STATEMENT},
        gasto_dividas_declarado_cent=150000,
    )
    compute = ComputeEngine().compute(consolidated)

    assert compute.total_descontos_cent == 100000
    assert compute.descontos_method == ComputeMethod.DIFFERENCE


@pytest.mark.unit
def test_total_descontos_fallback_declarado_sem_base_calculo():
    consolidator = ConsolidatorService()
    consolidated = consolidator.consolidate(
        payment_results=[_payment_result(bruto=None, liquido=4000.0, descontos=None)],
        loan_results=[],
        doc_sources={"payment_0": DocumentSource.PAYROLL_SALARY_STATEMENT},
        gasto_dividas_declarado_cent=90000,
    )
    compute = ComputeEngine().compute(consolidated)

    assert compute.total_descontos_cent == 90000
    assert compute.descontos_method == ComputeMethod.USER_DECLARED


@pytest.mark.unit
def test_extrato_only_com_declarados_nao_zera_campos():
    consolidator = ConsolidatorService()
    consolidated = consolidator.consolidate(
        payment_results=[],
        loan_results=[_loan_result()],
        doc_sources={},
        renda_mensal_declarada_cent=300000,
        gasto_dividas_declarado_cent=80000,
    )
    compute = ComputeEngine().compute(consolidated)

    assert compute.salario_liquido_cent == 300000
    assert compute.total_descontos_cent == 80000
    assert compute.descontos_method == ComputeMethod.USER_DECLARED
