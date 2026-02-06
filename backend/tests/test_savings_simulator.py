import pytest

from app.models.loan_contract import LoanContract
from app.services.savings_simulator import SavingsSimulator


@pytest.mark.unit
def test_simulate_refinancing_generates_positive_savings():
    contract = LoanContract(
        contract_key="abc",
        lender_name="Banco Teste",
        parcela_cent=53030,
        parcelas_restantes=12,
        taxa_juros="1,80%",
    )

    result = SavingsSimulator().simulate_refinancing([contract], taxa_referencia_mensal=1.5)

    assert result.economia_mensal_total_cent >= 0
    assert result.economia_total_restante_cent >= 0
    assert result.taxa_referencia_mensal_percent == "1,5%"
    assert "taxa de referência" in result.disclaimer


@pytest.mark.unit
def test_simulate_refinancing_ignores_invalid_contracts():
    invalid = LoanContract(
        contract_key="x",
        lender_name="Banco",
        parcela_cent=None,
        parcelas_restantes=None,
        taxa_juros=None,
    )
    result = SavingsSimulator().simulate_refinancing([invalid], taxa_referencia_mensal=1.5)
    assert result.contratos == []
