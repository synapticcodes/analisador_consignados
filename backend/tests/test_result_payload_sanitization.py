import pytest
from uuid import UUID

from app.models.inss_margin import INSSMargin
from app.services.result_payload import (
    has_inss_margin_data,
    sanitize_pii_text,
    truncate_alerts,
)


@pytest.mark.unit
def test_sanitize_pii_text_masks_cpf_and_long_numbers():
    source = "CPF 123.456.789-10 e benefício 12345678901234"
    sanitized = sanitize_pii_text(source)
    assert "***.***.***-**" in sanitized
    assert "************" in sanitized
    assert "123.456.789-10" not in sanitized


@pytest.mark.unit
def test_truncate_alerts_limits_length():
    alerts = ["x" * 70, "curto"]
    truncated = truncate_alerts(alerts, limit=50)
    assert len(truncated[0]) == 50
    assert truncated[1] == "curto"


@pytest.mark.unit
def test_has_margin_data_with_rmc_only():
    margin = INSSMargin(
        job_id=UUID("00000000-0000-0000-0000-000000000001"),
        source_file_id=None,
        base_calculo_cent=None,
        max_comprometimento_cent=None,
        total_comprometido_cent=None,
        margem_emprestimo_cent=None,
        margem_rmc_cent=None,
        margem_rcc_cent=None,
        cet_mensal=None,
        cet_anual=None,
        rmc_banco="BANCO TESTE",
        rmc_limite_cent=100000,
        rmc_reservado_cent=20000,
        evidence=None,
    )
    assert has_inss_margin_data(margin) is True
