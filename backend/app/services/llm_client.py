"""
LLM Client
~~~~~~~~~~

Wrapper para OpenAI API com retry, timeout e error handling.
"""

import json
from typing import Any

from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel

from app.core.config import settings


class LLMClient:
    """Cliente para comunicação com OpenAI API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ):
        """
        Inicializa o cliente LLM.

        Args:
            api_key: OpenAI API key (usa settings se não fornecido)
            model: Modelo a usar (usa settings se não fornecido)
            temperature: Temperature para sampling (0-2)
            max_tokens: Máximo de tokens na resposta
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.temperature = temperature
        self.max_tokens = max_tokens or settings.openai_max_tokens

        self.client = AsyncOpenAI(api_key=self.api_key)

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        response_format: type[BaseModel] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str | dict:
        """
        Executa chat completion.

        Args:
            messages: Lista de mensagens do chat
            response_format: Pydantic model para structured output (opcional)
            temperature: Override do temperature padrão
            max_tokens: Override do max_tokens padrão

        Returns:
            String com resposta ou dict se response_format for fornecido

        Raises:
            OpenAIError: Se ocorrer erro na API
        """
        try:
            completion_kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self.temperature,
            }

            # Add max_tokens if specified
            if max_tokens or self.max_tokens:
                completion_kwargs["max_tokens"] = max_tokens or self.max_tokens

            # Add response_format if specified (Structured Outputs)
            if response_format:
                completion_kwargs["response_format"] = response_format

            response = await self.client.chat.completions.create(**completion_kwargs)

            content = response.choices[0].message.content

            # Se response_format foi especificado, parse como JSON
            if response_format and content:
                return json.loads(content)

            return content or ""

        except OpenAIError as e:
            raise OpenAIError(f"Erro ao chamar OpenAI API: {str(e)}") from e

    async def chat_completion_with_retry(
        self,
        messages: list[dict[str, str]],
        response_format: type[BaseModel] | None = None,
        max_retries: int = 2,
    ) -> str | dict:
        """
        Executa chat completion com retry automático.

        Args:
            messages: Lista de mensagens
            response_format: Pydantic model para structured output
            max_retries: Número máximo de tentativas

        Returns:
            Resposta do modelo

        Raises:
            OpenAIError: Se todas as tentativas falharem
        """
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                return await self.chat_completion(
                    messages=messages, response_format=response_format
                )
            except OpenAIError as e:
                last_error = e
                if attempt < max_retries:
                    # Retry com backoff exponencial
                    import asyncio

                    await asyncio.sleep(2**attempt)
                    continue
                break

        raise OpenAIError(f"Falha após {max_retries + 1} tentativas: {last_error}") from last_error


class MockLLMClient(LLMClient):
    """
    Mock do LLM Client para testes e desenvolvimento.
    Retorna respostas pré-definidas ao invés de chamar OpenAI.
    """

    def __init__(self):
        """Inicializa mock client."""
        # Não chama super().__init__ para evitar necessidade de API key
        self.api_key = "mock"
        self.model = "gpt-4o-mock"
        self.temperature = 0.0
        self.max_tokens = 4096

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        response_format: type[BaseModel] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str | dict:
        """
        Mock de chat completion.

        Retorna resposta baseada no conteúdo da mensagem.
        """
        import asyncio

        await asyncio.sleep(0.1)  # Simular latência

        # Extrair último user message
        last_user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break

        # Extrair apenas o texto do documento (entre as marcas de código)
        document_text = ""
        if "**TEXTO DO DOCUMENTO" in last_user_message:
            parts = last_user_message.split("```")
            if len(parts) >= 3:
                # O texto do documento está no segundo bloco de código
                document_text = parts[1].strip().lower()

        # Se não encontrou, usar mensagem inteira
        if not document_text:
            document_text = last_user_message.lower()

        # Detectar tipo de operação baseado no prompt
        is_router = ("docFamily" in last_user_message or "Analise o texto abaixo e classifique" in last_user_message) and "EXTRAIA" not in last_user_message
        is_payment_extractor = "salarioBruto" in last_user_message or "linhasConsignado" in last_user_message or ("EXTRAIA" in last_user_message and ("folha de pagamento" in last_user_message.lower() or "PROVENTOS" in last_user_message))
        is_loan_extractor = "parcelaMensal" in last_user_message or "lenderName" in last_user_message or ("EXTRAIA" in last_user_message and "contrato de empréstimo" in last_user_message.lower())

        # Detectar tipo de documento baseado no texto do documento (não do prompt)
        is_payroll = False
        is_contract = False

        # Procurar por termos específicos de folha de pagamento
        if "proventos" in document_text and "descontos" in document_text:
            is_payroll = True
        elif "folha de pagamento" in document_text and "competência" in document_text:
            is_payroll = True

        # Procurar por termos de contrato
        if "contrato de empréstimo" in document_text:
            is_contract = True
        elif "número de parcelas" in document_text and "taxa de juros" in document_text:
            is_contract = True
        elif "contratante" in document_text and "contratado" in document_text:
            is_contract = True

        # Retornar resposta mock baseada no tipo de operação
        if is_payment_extractor and is_payroll:
            # Mock de Payment Extractor
            response_data = {
                "competencia": "2024-01",
                "salarioBruto": {
                    "value": 5500.00,
                    "currency": "BRL",
                    "method": "EXTRACTED_FROM_TOTAL_PROVENTOS",
                    "evidence": {
                        "page": 0,
                        "text": "Total de Proventos: R$ 5.500,00"
                    }
                },
                "salarioLiquido": {
                    "value": 4115.00,
                    "currency": "BRL",
                    "method": "EXTRACTED_FROM_LIQUIDO_RECEBER",
                    "evidence": {
                        "page": 0,
                        "text": "LÍQUIDO A RECEBER: R$ 4.115,00"
                    }
                },
                "totalDescontos": {
                    "value": 1385.00,
                    "currency": "BRL",
                    "method": "EXTRACTED_FROM_TOTAL_DESCONTOS",
                    "evidence": {
                        "page": 0,
                        "text": "Total de Descontos: R$ 1.385,00"
                    }
                },
                "linhasConsignado": [
                    {
                        "descricao": "Consignado Banco ABC",
                        "rubrica": "216",
                        "valorCent": 25000,
                        "evidence": {
                            "page": 0,
                            "text": "Consignado Banco ABC (216): R$ 250,00"
                        }
                    },
                    {
                        "descricao": "Consignado Banco XYZ",
                        "rubrica": "217",
                        "valorCent": 18000,
                        "evidence": {
                            "page": 0,
                            "text": "Consignado Banco XYZ (217): R$ 180,00"
                        }
                    }
                ],
                "alerts": []
            }
            return json.dumps(response_data)

        elif is_loan_extractor and is_contract:
            # Mock de Loan Extractor
            response_data = {
                "lenderName": "Banco Exemplo S.A.",
                "contractId": "123456789",
                "parcelaMensal": {
                    "value": 350.00,
                    "currency": "BRL",
                    "method": "EXTRACTED_FROM_CONTRACT",
                    "evidence": {
                        "page": 0,
                        "text": "Valor da Parcela: R$ 350,00"
                    }
                },
                "totalParcelas": 36,
                "parcelasPagas": None,
                "parcelasRestantes": None,
                "valorTotal": {
                    "value": 10000.00,
                    "currency": "BRL",
                    "method": "EXTRACTED_FROM_CONTRACT",
                    "evidence": {
                        "page": 0,
                        "text": "Valor Total do Contrato: R$ 10.000,00"
                    }
                },
                "taxaJuros": "2.5% a.m.",
                "alerts": []
            }
            return json.dumps(response_data)

        elif is_router and is_payroll:
            response_data = {
                "docFamily": "PAYROLL_SALARY_STATEMENT",
                "confidence": 0.95,
                "capabilities": [
                    "PROVIDES_GROSS_NET_DEDUCTIONS",
                    "PROVIDES_CONSIGNADO_LINES",
                ],
                "competenciasDetectadas": ["2024-01"],
                "evidence": [
                    {
                        "page": 0,
                        "text": "FOLHA DE PAGAMENTO - 01/2024",
                    }
                ],
            }
            return json.dumps(response_data)

        elif is_contract:
            response_data = {
                "docFamily": "LOAN_CONTRACT_GENERIC",
                "confidence": 0.92,
                "capabilities": ["PROVIDES_LOAN_CONTRACTS"],
                "competenciasDetectadas": [],
                "evidence": [
                    {
                        "page": 0,
                        "text": "CONTRATO DE EMPRÉSTIMO CONSIGNADO",
                    }
                ],
            }
            return json.dumps(response_data)

        else:
            # Mock de resposta genérica para documento desconhecido
            response_data = {
                "docFamily": "OTHER_UNKNOWN",
                "confidence": 0.3,
                "capabilities": [],
                "competenciasDetectadas": [],
                "evidence": [],
            }
            return json.dumps(response_data)

    async def chat_completion_with_retry(
        self,
        messages: list[dict[str, str]],
        response_format: type[BaseModel] | None = None,
        max_retries: int = 2,
    ) -> str | dict:
        """Mock sempre retorna na primeira tentativa."""
        return await self.chat_completion(
            messages=messages, response_format=response_format
        )
