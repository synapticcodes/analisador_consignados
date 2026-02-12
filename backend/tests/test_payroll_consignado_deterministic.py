import json

import pytest

from app.services.extractors import PaymentExtractor


class StubLLMClient:
    async def chat_completion_with_retry(self, messages, max_retries=1):
        return json.dumps(
            {
                "competencia": "2026-01",
                "salarioBruto": None,
                "salarioLiquido": None,
                "totalDescontos": None,
                "linhasConsignado": [],
                "alerts": [],
            }
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_deterministic_consignado_lines_in_descontos():
    text = """
FOLHA DE PAGAMENTO
COMPETENCIA: 01/2026

DESCONTOS
085
150,00
EMPREST BCO PRIVADOS - PRB
086
417,00
EMPREST BCO PRIVADOS - PRB
EMPREST BCO PRIVADOS - PRB
95,00
EMPREST BCO PRIVADOS - PRB 445,44
IRRF
350,00
TOTAL DE DESCONTOS

LIQUIDO A RECEBER
"""
    extractor = PaymentExtractor(llm_client=StubLLMClient())
    result = await extractor.extract(text=text, competencia="2026-01")
    valores = {linha.valor_cent for linha in result.linhas_consignado}
    linha_completa = next((linha for linha in result.linhas_consignado if linha.rubrica == "086"), None)

    assert 15000 in valores
    assert 41700 in valores
    assert 9500 in valores
    assert 44544 in valores
    assert linha_completa is not None
    assert linha_completa.descricao_raw is not None
    assert linha_completa.descricao_canonica is not None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_payroll_summary_fallback_extracts_bruto_liquido_descontos():
    text = """
COMPROVANTE DE RENDIMENTOS - FOLHA
COMPETENCIA: 01/2026

RENDIMENTOS
...
DESCONTOS
...

BRUTO
15.065,86
DESCONTO
8.668,98
LÍQUIDO
6.396,88
"""
    extractor = PaymentExtractor(llm_client=StubLLMClient())
    result = await extractor.extract(text=text, competencia="2026-01")

    assert result.salario_bruto.value == 15065.86
    assert result.salario_liquido.value == 6396.88
    assert result.total_descontos.value == 8668.98
    assert result.salario_bruto.method == "EXTRACTED_FROM_BRUTO_SUMMARY"
    assert result.salario_liquido.method == "EXTRACTED_FROM_LIQUIDO_SUMMARY"
    assert result.total_descontos.method == "EXTRACTED_FROM_DESCONTOS_SUMMARY"
