import pytest

from app.models.loan_contract import LoanContract
from app.services.compute_engine import ComputeEngine


@pytest.mark.unit
def test_compute_contract_costs_returns_expected_values():
    contract = LoanContract(
        contract_key="cost-1",
        lender_name="Banco Exemplo",
        contract_id="123",
        parcela_cent=53030,
        parcelas_restantes=12,
        valor_emprestado_cent=526513,
    )

    items, total = ComputeEngine().compute_contract_costs([contract])

    assert len(items) == 1
    assert items[0]["total_a_pagar_cent"] == 636360
    assert items[0]["custo_juros_cent"] == 109847
    assert total == 109847
