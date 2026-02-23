import pytest

from app.services.router import DocumentFamily, RouterService


class FailingLLMClient:
    async def chat_completion_with_retry(self, messages, max_retries=1):
        raise RuntimeError("sem credenciais OpenAI")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_router_heuristic_detects_comprovante_rendimentos_as_payroll():
    router = RouterService(llm_client=FailingLLMClient())
    text = """
COMPROVANTE DE RENDIMENTOS - FOLHA
RENDIMENTOS
DESCONTOS
LÍQUIDO
"""

    result = await router.classify_document(text=text, metadata={"filename": "contracheque.pdf"})

    assert result.doc_family == DocumentFamily.PAYROLL_SALARY_STATEMENT.value
    assert result.confidence >= 0.5
