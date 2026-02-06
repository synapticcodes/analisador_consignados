import pytest

from app.services.extractors import LoanExtractor
from app.services.llm_client import MockLLMClient


@pytest.mark.unit
def test_extract_inss_margin_data_parses_core_fields():
    extractor = LoanExtractor(llm_client=MockLLMClient())
    text = """
    Margem para Empréstimo/Cartão e Resumo Financeiro
    BASE DE CÁLCULO R$ 1.621,00
    MÁXIMO DE COMPROMETIMENTO R$ 729,45
    TOTAL COMPROMETIDO R$ 611,35
    MARGEM DISPONÍVEL - EMPRÉSTIMO R$ 37,05
    MARGEM DISPONÍVEL - RMC R$ 0,00
    MARGEM DISPONÍVEL - RCC R$ 81,05
    CET MENSAL 1,81%
    CET ANUAL 24,14%
    """

    parsed = extractor.extract_inss_margin_data(text)
    assert parsed is not None
    assert parsed["base_calculo_cent"] == 162100
    assert parsed["total_comprometido_cent"] == 61135
    assert parsed["margem_rmc_cent"] == 0
    assert parsed["cet_mensal"] == "1,81%"


@pytest.mark.unit
def test_extract_inss_historical_contracts_returns_list():
    extractor = LoanExtractor(llm_client=MockLLMClient())
    text = """
    CONTRATOS EXCLUÍDOS E ENCERRADOS
    121 - BANCO AGIBANK
    Contrato 123456789
    01/01/2020 01/01/2024
    PARCELA R$ 250,00
    VALOR EMPRESTADO R$ 4.500,00
    Encerrado por refinanciamento
    CARTÃO DE CRÉDITO
    """

    items = extractor.extract_inss_historical_contracts(text)
    assert len(items) == 1
    assert items[0]["contract_id"] == "123456789"
    assert items[0]["parcela_cent"] == 25000


@pytest.mark.unit
def test_extract_inss_margin_data_keeps_rmc_without_base():
    extractor = LoanExtractor(llm_client=MockLLMClient())
    text = """
    CARTÃO DE CRÉDITO
    Banco: BANCO TESTE
    Limite R$ 1.000,00
    Reservado R$ 140,00
    """

    parsed = extractor.extract_inss_margin_data(text)
    assert parsed is not None
    assert parsed["rmc_banco"] == "BANCO TESTE"
    assert parsed["rmc_limite_cent"] == 100000
    assert parsed["rmc_reservado_cent"] == 14000


@pytest.mark.unit
def test_contract_fallback_does_not_use_valor_emprestado_as_valor_total():
    extractor = LoanExtractor(llm_client=MockLLMClient())
    text = """
EMPRÉSTIMOS BANCÁRIOS
121 - BANCO TESTE
123456789012
12
PARCELA R$ 530,30
EMPRESTADO LIBERADO R$ 5.593,83
ATIVO
"""

    contracts = extractor._extract_contracts_from_text(text, fallback_alert=None)
    assert len(contracts) == 1
    contract = contracts[0]
    assert contract.parcela_mensal.value == 530.30
    assert contract.total_parcelas == 12
    assert contract.valor_total.value is None
    assert contract.valor_emprestado_cent == 559383


@pytest.mark.unit
def test_merge_contracts_keeps_unmatched_fallback_items():
    extractor = LoanExtractor(llm_client=MockLLMClient())
    primary = []
    fallback = [
        extractor._extract_contracts_from_text(
            """
            EMPRÉSTIMOS BANCÁRIOS
            121 - BANCO A
            111111111111
            12
            PARCELA R$ 100,00
            ATIVO
            """,
            fallback_alert=None,
        )[0],
        extractor._extract_contracts_from_text(
            """
            EMPRÉSTIMOS BANCÁRIOS
            122 - BANCO B
            222222222222
            24
            PARCELA R$ 200,00
            ATIVO
            """,
            fallback_alert=None,
        )[0],
    ]

    merged = extractor._merge_contracts(primary, fallback)
    ids = {item.contract_id for item in merged}
    assert "111111111111" in ids
    assert "222222222222" in ids
