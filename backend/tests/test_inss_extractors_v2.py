import pytest

from app.services.extractors import ExtractedField, LoanContractResult, LoanExtractor
from app.services.llm_client import MockLLMClient


class StubLoanListLLMClient:
    async def chat_completion_with_retry(self, messages, max_retries=1):
        return {
            "contracts": [
                {
                    "lenderName": "BANCO TESTE",
                    "contractId": "1234567890",
                    "parcelaMensal": {
                        "value": 530.30,
                        "currency": "BRL",
                        "method": "EXTRACTED",
                        "evidence": {"page": 0, "text": "R$530,30"},
                    },
                    "valorTotal": {
                        "value": 5593.83,
                        "currency": "BRL",
                        "method": "EXTRACTED",
                        "evidence": {"page": 0, "text": "R$5.593,83"},
                    },
                    "totalParcelas": 12,
                    "iof": "R$ 7,45",
                    "valorEmprestado": "R$ 5.593,83",
                    "alerts": [],
                }
            ],
            "alerts": [],
        }


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


@pytest.mark.unit
def test_contract_fallback_parses_split_bank_line():
    extractor = LoanExtractor(llm_client=MockLLMClient())
    text = """
EMPRÉSTIMOS BANCÁRIOS
CONTRATOS ATIVOS E SUSPENSOS
153928
2128
121 -
BANCO
AGIBAN
K SA
11/2025
10/2026
12
R$530,30
R$5.593,83
ATIVO
"""

    contracts = extractor._extract_contracts_from_text(text, fallback_alert=None)
    assert len(contracts) == 1
    contract = contracts[0]
    assert contract.contract_id == "1539282128"
    assert contract.lender_name == "BANCO AGIBAN K SA"
    assert contract.parcela_mensal.value == 530.30
    assert contract.total_parcelas == 12
    assert contract.parcelas_restantes == 12


@pytest.mark.unit
def test_contract_fallback_parses_inss_tabular_columns():
    extractor = LoanExtractor(llm_client=MockLLMClient())
    text = """
EMPRÉSTIMOS BANCÁRIOS
CONTRATOS ATIVOS E SUSPENSOS
153928
2128
121 -
BANCO
AGIBAN
K SA
11/2025 10/2026 12 R$530,30 R$5.593,83 R$7,
45Ativo
Averbação por refinanciamento
13/10/25 1,81 24,14 1,80 23,87 R$5.265,13 08/12/25
"""

    contracts = extractor._extract_contracts_from_text(text, fallback_alert=None)
    assert len(contracts) == 1
    contract = contracts[0]
    assert contract.contract_id == "1539282128"
    assert contract.total_parcelas == 12
    assert contract.parcelas_restantes == 12
    assert contract.valor_emprestado_cent == 559383
    assert contract.iof_cent == 745
    assert contract.cet_mensal == "1,81%"
    assert contract.cet_anual == "24,14%"
    assert contract.taxa_juros == "1,80%"


@pytest.mark.unit
def test_merge_contracts_enriches_partial_llm_contract_by_parcela():
    extractor = LoanExtractor(llm_client=MockLLMClient())
    primary = [
        LoanContractResult(
            lender_name="BANCO AGIBANK SA",
            contract_id="153928",
            parcela_mensal=ExtractedField(
                value=530.30,
                currency="BRL",
                method="EXTRACTED_FROM_STATEMENT",
                evidence=None,
            ),
            total_parcelas=None,
            parcelas_pagas=None,
            parcelas_restantes=None,
            valor_total=ExtractedField(
                value=5593.83,
                currency="BRL",
                method="EXTRACTED_FROM_STATEMENT",
                evidence=None,
            ),
            taxa_juros="1,80",
            alerts=[],
            status="ATIVO",
            cet_mensal=None,
            cet_anual=None,
            iof_cent=None,
            valor_emprestado_cent=None,
        )
    ]
    fallback = extractor._extract_contracts_from_text(
        """
EMPRÉSTIMOS BANCÁRIOS
CONTRATOS ATIVOS E SUSPENSOS
153928
2128
121 -
BANCO
AGIBAN
K SA
11/2025 10/2026 12 R$530,30 R$5.593,83 R$7,
45Ativo
Averbação por refinanciamento
13/10/25 1,81 24,14 1,80 23,87 R$5.265,13 08/12/25
""",
        fallback_alert=None,
    )

    merged = extractor._merge_contracts(primary, fallback)
    assert len(merged) == 1
    contract = merged[0]
    assert contract.contract_id == "1539282128"
    assert contract.total_parcelas == 12
    assert contract.parcelas_restantes == 12
    assert contract.cet_mensal == "1,81%"
    assert contract.cet_anual == "24,14%"
    assert contract.taxa_juros == "1,80"
    assert contract.iof_cent == 745
    assert contract.valor_emprestado_cent == 559383


@pytest.mark.asyncio
@pytest.mark.unit
async def test_extract_many_keeps_lender_name_and_parses_cent_fields():
    extractor = LoanExtractor(llm_client=StubLoanListLLMClient())
    contracts = await extractor.extract_many("texto qualquer")

    assert len(contracts) == 1
    contract = contracts[0]
    assert contract.lender_name == "BANCO TESTE"
    assert contract.contract_id == "1234567890"
    assert contract.iof_cent == 745
    assert contract.valor_emprestado_cent == 559383
