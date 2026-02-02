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

    assert 15000 in valores
    assert 41700 in valores
    assert 9500 in valores
    assert 44544 in valores
