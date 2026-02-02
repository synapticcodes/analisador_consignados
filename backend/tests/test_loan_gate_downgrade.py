import pytest


@pytest.mark.unit
def test_loan_gate_downgrades_parcela_when_bank_and_total_present():
    from app.services.evidence_gate import EvidenceGate
    from app.services.extractors import ExtractedField, FieldEvidence, LoanContractResult

    result = LoanContractResult(
        lender_name="Banco Exemplo",
        contract_id="123",
        parcela_mensal=ExtractedField(
            value=100.00,
            currency="BRL",
            method="EXTRACTED_FROM_STATEMENT",
            evidence=FieldEvidence(page=0, text="R$200,00"),
        ),
        total_parcelas=None,
        parcelas_pagas=None,
        parcelas_restantes=None,
        valor_total=ExtractedField(
            value=1000.00,
            currency="BRL",
            method="EXTRACTED_FROM_STATEMENT",
            evidence=FieldEvidence(page=0, text="R$1.000,00"),
        ),
        taxa_juros=None,
        alerts=[],
    )

    gate = EvidenceGate(tolerance=0.01)
    gate_result = gate.validate_loan_extraction(result)

    assert gate_result.gate_status.value == "WARN"
    assert any(
        alert.field_name == "parcelaMensal" and not alert.is_critical
        for alert in gate_result.alerts
    )
