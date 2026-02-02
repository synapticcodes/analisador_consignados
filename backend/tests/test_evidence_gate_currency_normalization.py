import pytest


@pytest.mark.unit
def test_parse_best_match_handles_split_decimal():
    from app.services.evidence_gate import EvidenceGate

    gate = EvidenceGate(tolerance=0.01)
    value = gate._parse_best_match("R$1.660,2\n8", 1660.28)
    assert value is not None
    assert abs(value - 1660.28) < 0.001
