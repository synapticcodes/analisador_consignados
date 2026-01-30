"""
Extractors LLM Service
~~~~~~~~~~~~~~~~~~~~~~

Extrai dados estruturados de documentos financeiros.
- Payment Extractor: Folhas de pagamento e extratos INSS
- Loan Extractor: Contratos de empréstimo consignado

Baseado no PRD seção RF-006.
"""

from dataclasses import dataclass
import json
import re

from app.services.llm_client import LLMClient


@dataclass
class FieldEvidence:
    """Evidência para um campo extraído."""

    page: int
    text: str


@dataclass
class ExtractedField:
    """Campo extraído com evidência."""

    value: str | float | None
    currency: str | None
    method: str | None
    evidence: FieldEvidence | None


@dataclass
class ConsignadoLine:
    """Linha individual de consignado."""

    descricao: str
    rubrica: str | None
    valor_cent: int
    evidence: FieldEvidence


@dataclass
class PaymentExtractionResult:
    """Resultado da extração de folha de pagamento."""

    competencia: str
    salario_bruto: ExtractedField
    salario_liquido: ExtractedField
    total_descontos: ExtractedField
    linhas_consignado: list[ConsignadoLine]
    alerts: list[str]


@dataclass
class LoanContractResult:
    """Resultado da extração de contrato de empréstimo."""

    lender_name: str | None
    contract_id: str | None
    parcela_mensal: ExtractedField
    total_parcelas: int | None
    parcelas_pagas: int | None
    parcelas_restantes: int | None
    valor_total: ExtractedField
    taxa_juros: str | None
    alerts: list[str]


class PaymentExtractor:
    """
    Extrator de dados de folha de pagamento.

    Extrai: salário bruto, líquido, descontos e linhas de consignado.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Inicializa o Payment Extractor.

        Args:
            llm_client: Cliente LLM para comunicação com OpenAI
        """
        self.llm_client = llm_client

    def _build_payment_prompt(self, text: str, competencia: str | None) -> str:
        """
        Constrói o prompt do Payment Extractor baseado no PRD seção 10.2.

        Args:
            text: Texto completo do documento
            competencia: Competência detectada pelo Router (opcional)

        Returns:
            Prompt formatado
        """
        return f"""Você é um extrator de dados financeiros especializado em folhas de pagamento brasileiras.

**TAREFA:** Extraia os dados estruturados da folha de pagamento abaixo.

**REGRAS CRÍTICAS:**
1. NUNCA execute somas ou cálculos - apenas EXTRAIA valores que aparecem no documento
2. Cada valor deve incluir evidência (trecho exato do texto + página)
3. Se um campo não existir, retorne value=null + alerta explicativo
4. Linhas de consignado devem ser extraídas INDIVIDUALMENTE (não somar)
5. Retorne JSON válido seguindo o schema exato

**CAMPOS A EXTRAIR:**
- salarioBruto: Salário bruto / Total de proventos
- salarioLiquido: Salário líquido / Líquido a receber
- totalDescontos: Total de descontos (opcional, pode ser calculado depois)
- linhasConsignado: Array de linhas de consignado individuais

**RUBRICAS DE CONSIGNADO CONHECIDAS:** 216, 217, 268, "CONSIGNACAO", "EMPRESTIMO", "EMPREST", "CONS"

**COMPETÊNCIA ESPERADA:** {competencia or 'Detectar do documento'}

**TEXTO DO DOCUMENTO:**
```
{text}
```

**RESPOSTA (JSON):**
{{
  "competencia": "2024-01",
  "salarioBruto": {{
    "value": 5500.00,
    "currency": "BRL",
    "method": "EXTRACTED_FROM_TOTAL_PROVENTOS",
    "evidence": {{
      "page": 0,
      "text": "Total de Proventos: R$ 5.500,00"
    }}
  }},
  "salarioLiquido": {{
    "value": 4115.00,
    "currency": "BRL",
    "method": "EXTRACTED_FROM_LIQUIDO_RECEBER",
    "evidence": {{
      "page": 0,
      "text": "Líquido a Receber: R$ 4.115,00"
    }}
  }},
  "totalDescontos": {{
    "value": 1385.00,
    "currency": "BRL",
    "method": "EXTRACTED_FROM_TOTAL_DESCONTOS",
    "evidence": {{
      "page": 0,
      "text": "Total de Descontos: R$ 1.385,00"
    }}
  }},
  "linhasConsignado": [
    {{
      "descricao": "Consignado Banco ABC",
      "rubrica": "216",
      "valorCent": 25000,
      "evidence": {{
        "page": 0,
        "text": "Consignado Banco ABC (216): R$ 250,00"
      }}
    }},
    {{
      "descricao": "Consignado Banco XYZ",
      "rubrica": "217",
      "valorCent": 18000,
      "evidence": {{
        "page": 0,
        "text": "Consignado Banco XYZ (217): R$ 180,00"
      }}
    }}
  ],
  "alerts": []
}}
"""

    async def extract(
        self, text: str, competencia: str | None = None
    ) -> PaymentExtractionResult:
        """
        Extrai dados de folha de pagamento.

        Args:
            text: Texto completo do documento
            competencia: Competência detectada pelo Router

        Returns:
            PaymentExtractionResult com dados extraídos

        Raises:
            ValueError: Se resposta do LLM for inválida
        """
        # Construir prompt
        prompt = self._build_payment_prompt(text, competencia)

        # Chamar LLM
        messages = [
            {
                "role": "system",
                "content": "Você é um extrator de dados financeiros. Retorne apenas JSON válido.",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            # Chamar com retry (RF-006 FE-001)
            response = await self.llm_client.chat_completion_with_retry(
                messages=messages, max_retries=1
            )

            # Parse response
            def _safe_json_loads(payload: str) -> dict:
                try:
                    return json.loads(payload)
                except Exception:
                    start = payload.find("{")
                    end = payload.rfind("}")
                    if start != -1 and end != -1 and end > start:
                        return json.loads(payload[start : end + 1])
                    raise

            if isinstance(response, str):
                result_dict = _safe_json_loads(response)
            else:
                result_dict = response

            # Extrair campos
            def parse_field(field_dict: dict | None) -> ExtractedField:
                if not field_dict or field_dict.get("value") is None:
                    return ExtractedField(
                        value=None, currency=None, method=None, evidence=None
                    )

                ev = field_dict.get("evidence", {})
                evidence = (
                    FieldEvidence(page=ev.get("page", 0), text=ev.get("text", ""))
                    if ev
                    else None
                )

                return ExtractedField(
                    value=field_dict.get("value"),
                    currency=field_dict.get("currency", "BRL"),
                    method=field_dict.get("method"),
                    evidence=evidence,
                )

            # Extrair linhas de consignado
            linhas = []
            for linha_dict in result_dict.get("linhasConsignado", []):
                ev = linha_dict.get("evidence", {})
                evidence = FieldEvidence(page=ev.get("page", 0), text=ev.get("text", ""))

                linhas.append(
                    ConsignadoLine(
                        descricao=linha_dict.get("descricao", ""),
                        rubrica=linha_dict.get("rubrica"),
                        valor_cent=linha_dict.get("valorCent", 0),
                        evidence=evidence,
                    )
                )

            return PaymentExtractionResult(
                competencia=result_dict.get("competencia", ""),
                salario_bruto=parse_field(result_dict.get("salarioBruto")),
                salario_liquido=parse_field(result_dict.get("salarioLiquido")),
                total_descontos=parse_field(result_dict.get("totalDescontos")),
                linhas_consignado=linhas,
                alerts=result_dict.get("alerts", []),
            )

        except Exception as e:
            # RF-006 FE-001: Se falhar, retorna resultado vazio com alerta
            return PaymentExtractionResult(
                competencia="",
                salario_bruto=ExtractedField(None, None, None, None),
                salario_liquido=ExtractedField(None, None, None, None),
                total_descontos=ExtractedField(None, None, None, None),
                linhas_consignado=[],
                alerts=[f"Erro ao extrair dados: {str(e)}"],
            )


class LoanExtractor:
    """
    Extrator de dados de contratos de empréstimo consignado.

    Extrai: banco, parcela mensal, total parcelas, saldo devedor, etc.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Inicializa o Loan Extractor.

        Args:
            llm_client: Cliente LLM para comunicação com OpenAI
        """
        self.llm_client = llm_client

    def _build_loan_prompt(self, text: str) -> str:
        """
        Constrói o prompt do Loan Extractor baseado no PRD seção 10.3.

        Args:
            text: Texto completo do documento

        Returns:
            Prompt formatado
        """
        return f"""Você é um extrator de dados financeiros especializado em contratos de empréstimo consignado brasileiros.

**TAREFA:** Extraia os dados estruturados do contrato de empréstimo abaixo.

**REGRAS CRÍTICAS:**
1. NUNCA execute somas ou cálculos - apenas EXTRAIA valores que aparecem no documento
2. Cada valor deve incluir evidência (trecho exato do texto + página)
3. Se um campo não existir, retorne value=null + alerta explicativo
4. Retorne JSON válido seguindo o schema exato

**CAMPOS A EXTRAIR:**
- lenderName: Nome do banco/instituição financeira
- contractId: Número do contrato (se disponível)
- parcelaMensal: Valor da parcela mensal
- totalParcelas: Número total de parcelas
- parcelasPagas: Parcelas já pagas (se disponível)
- parcelasRestantes: Parcelas restantes (se disponível)
- valorTotal: Valor total do contrato
- taxaJuros: Taxa de juros (se disponível)

**TEXTO DO DOCUMENTO:**
```
{text}
```

**RESPOSTA (JSON):**
{{
  "lenderName": "Banco Exemplo S.A.",
  "contractId": "123456789",
  "parcelaMensal": {{
    "value": 350.00,
    "currency": "BRL",
    "method": "EXTRACTED_FROM_CONTRACT",
    "evidence": {{
      "page": 0,
      "text": "Valor da Parcela: R$ 350,00"
    }}
  }},
  "totalParcelas": 36,
  "parcelasPagas": null,
  "parcelasRestantes": null,
  "valorTotal": {{
    "value": 10000.00,
    "currency": "BRL",
    "method": "EXTRACTED_FROM_CONTRACT",
    "evidence": {{
      "page": 0,
      "text": "Valor Total do Contrato: R$ 10.000,00"
    }}
  }},
  "taxaJuros": "2.5% a.m.",
  "alerts": []
}}
"""

    def _build_loan_list_prompt(self, text: str) -> str:
        """
        Constrói o prompt para extrair múltiplos contratos de extrato consignado.

        Args:
            text: Texto completo do documento

        Returns:
            Prompt formatado
        """
        return f"""Você é um extrator de dados financeiros especializado em extratos de empréstimos consignados do INSS.

**TAREFA:** Extraia TODOS os contratos de empréstimo consignado presentes no documento.

**REGRAS CRÍTICAS:**
1. NUNCA execute somas ou cálculos - apenas EXTRAIA valores que aparecem no documento
2. Cada valor monetário deve incluir evidência (trecho exato do texto + página)
3. Se um campo não existir, retorne value=null + alerta explicativo
4. Retorne JSON válido seguindo o schema exato
5. Extraia SOMENTE contratos na seção **“EMPRÉSTIMOS BANCÁRIOS — CONTRATOS ATIVOS E SUSPENSOS”**
6. IGNORE completamente a seção **“CONTRATOS EXCLUÍDOS E ENCERRADOS”**
7. IGNORE cartões (RMC/RCC) e descontos de cartão

**CAMPOS A EXTRAIR POR CONTRATO:**
- lenderName: Nome do banco/instituição financeira
- contractId: Número do contrato (se disponível)
- parcelaMensal: Valor da parcela mensal
- totalParcelas: Número total de parcelas
- parcelasPagas: Parcelas já pagas (se disponível)
- parcelasRestantes: Parcelas restantes (se disponível)
- valorTotal: Valor total do contrato
- taxaJuros: Taxa de juros (se disponível)

**TEXTO DO DOCUMENTO:**
```
{text}
```

**RESPOSTA (JSON):**
{{
  "contracts": [
    {{
      "lenderName": "Banco Exemplo S.A.",
      "contractId": "123456789",
      "parcelaMensal": {{
        "value": 350.00,
        "currency": "BRL",
        "method": "EXTRACTED_FROM_STATEMENT",
        "evidence": {{
          "page": 0,
          "text": "Valor da Parcela: R$ 350,00"
        }}
      }},
      "totalParcelas": 36,
      "parcelasPagas": null,
      "parcelasRestantes": null,
      "valorTotal": {{
        "value": 10000.00,
        "currency": "BRL",
        "method": "EXTRACTED_FROM_STATEMENT",
        "evidence": {{
          "page": 0,
          "text": "Valor Total do Contrato: R$ 10.000,00"
        }}
      }},
      "taxaJuros": "2.5% a.m.",
      "alerts": []
    }}
  ],
  "alerts": []
}}
"""

    async def extract(self, text: str) -> LoanContractResult:
        """
        Extrai dados de contrato de empréstimo.

        Args:
            text: Texto completo do documento

        Returns:
            LoanContractResult com dados extraídos

        Raises:
            ValueError: Se resposta do LLM for inválida
        """
        # Construir prompt
        prompt = self._build_loan_prompt(text)

        # Chamar LLM
        messages = [
            {
                "role": "system",
                "content": "Você é um extrator de dados financeiros. Retorne apenas JSON válido.",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            # Chamar com retry
            response = await self.llm_client.chat_completion_with_retry(
                messages=messages, max_retries=1
            )

            # Parse response
            def _safe_json_loads(payload: str) -> dict:
                try:
                    return json.loads(payload)
                except Exception:
                    start = payload.find("{")
                    end = payload.rfind("}")
                    if start != -1 and end != -1 and end > start:
                        return json.loads(payload[start : end + 1])
                    raise

            if isinstance(response, str):
                result_dict = _safe_json_loads(response)
            else:
                result_dict = response

            # Extrair campos
            def parse_field(field_dict: dict | None) -> ExtractedField:
                if not field_dict or field_dict.get("value") is None:
                    return ExtractedField(
                        value=None, currency=None, method=None, evidence=None
                    )

                ev = field_dict.get("evidence", {})
                evidence = (
                    FieldEvidence(page=ev.get("page", 0), text=ev.get("text", ""))
                    if ev
                    else None
                )

                return ExtractedField(
                    value=field_dict.get("value"),
                    currency=field_dict.get("currency", "BRL"),
                    method=field_dict.get("method"),
                    evidence=evidence,
                )

            def parse_int_field(raw_value) -> int | None:
                if raw_value is None:
                    return None
                if isinstance(raw_value, dict):
                    raw_value = raw_value.get("value")
                if raw_value is None:
                    return None
                if isinstance(raw_value, bool):
                    return None
                if isinstance(raw_value, int):
                    return raw_value
                if isinstance(raw_value, float):
                    return int(raw_value) if raw_value.is_integer() else None
                if isinstance(raw_value, str):
                    match = re.search(r"-?\d+", raw_value.strip())
                    return int(match.group(0)) if match else None
                return None

            return LoanContractResult(
                lender_name=result_dict.get("lenderName"),
                contract_id=result_dict.get("contractId"),
                parcela_mensal=parse_field(result_dict.get("parcelaMensal")),
                total_parcelas=parse_int_field(result_dict.get("totalParcelas")),
                parcelas_pagas=parse_int_field(result_dict.get("parcelasPagas")),
                parcelas_restantes=parse_int_field(result_dict.get("parcelasRestantes")),
                valor_total=parse_field(result_dict.get("valorTotal")),
                taxa_juros=result_dict.get("taxaJuros"),
                alerts=result_dict.get("alerts", []),
            )

        except Exception as e:
            # Se falhar, retorna resultado vazio com alerta
            return LoanContractResult(
                lender_name=None,
                contract_id=None,
                parcela_mensal=ExtractedField(None, None, None, None),
                total_parcelas=None,
                parcelas_pagas=None,
                parcelas_restantes=None,
                valor_total=ExtractedField(None, None, None, None),
                taxa_juros=None,
                alerts=[f"Erro ao extrair dados do contrato: {str(e)}"],
            )

    async def extract_many(self, text: str) -> list[LoanContractResult]:
        """
        Extrai múltiplos contratos de empréstimo (extratos consignados).

        Args:
            text: Texto completo do documento

        Returns:
            Lista de LoanContractResult
        """
        prompt = self._build_loan_list_prompt(text)

        messages = [
            {
                "role": "system",
                "content": "Você é um extrator de dados financeiros. Retorne apenas JSON válido.",
            },
            {"role": "user", "content": prompt},
        ]

        async def _request_payload(prompt_text: str) -> str | dict:
            request_messages = [
                {
                    "role": "system",
                    "content": "Você é um extrator de dados financeiros. Retorne apenas JSON válido.",
                },
                {"role": "user", "content": prompt_text},
            ]
            return await self.llm_client.chat_completion_with_retry(
                messages=request_messages, max_retries=1
            )

        try:
            response = await _request_payload(prompt)

            def _safe_json_loads(payload: str) -> dict | list:
                payload = payload.strip()
                if not payload:
                    raise ValueError("Resposta vazia do modelo")
                try:
                    return json.loads(payload)
                except Exception:
                    if "```" in payload:
                        parts = payload.split("```")
                        for part in parts:
                            cleaned = part.strip()
                            if cleaned.startswith("{") or cleaned.startswith("["):
                                return json.loads(cleaned)
                    start = payload.find("{")
                    end = payload.rfind("}")
                    if start != -1 and end != -1 and end > start:
                        return json.loads(payload[start : end + 1])
                    start = payload.find("[")
                    end = payload.rfind("]")
                    if start != -1 and end != -1 and end > start:
                        return json.loads(payload[start : end + 1])
                    raise

            if isinstance(response, str):
                try:
                    result_payload = _safe_json_loads(response)
                except Exception:
                    # Retry com texto truncado e instrução explícita
                    short_prompt = self._build_loan_list_prompt(text[:8000])
                    short_prompt += "\n\nResponda SOMENTE com JSON válido, sem comentários."
                    retry_response = await _request_payload(short_prompt)
                    if isinstance(retry_response, str):
                        result_payload = _safe_json_loads(retry_response)
                    else:
                        result_payload = retry_response
            else:
                result_payload = response

            # Extrair campos
            def parse_field(field_dict: dict | None) -> ExtractedField:
                if not field_dict or field_dict.get("value") is None:
                    return ExtractedField(
                        value=None, currency=None, method=None, evidence=None
                    )

                ev = field_dict.get("evidence", {})
                evidence = (
                    FieldEvidence(page=ev.get("page", 0), text=ev.get("text", ""))
                    if ev
                    else None
                )

                return ExtractedField(
                    value=field_dict.get("value"),
                    currency=field_dict.get("currency", "BRL"),
                    method=field_dict.get("method"),
                    evidence=evidence,
                )

            def parse_int_field(raw_value) -> int | None:
                if raw_value is None:
                    return None
                if isinstance(raw_value, dict):
                    raw_value = raw_value.get("value")
                if raw_value is None:
                    return None
                if isinstance(raw_value, bool):
                    return None
                if isinstance(raw_value, int):
                    return raw_value
                if isinstance(raw_value, float):
                    return int(raw_value) if raw_value.is_integer() else None
                if isinstance(raw_value, str):
                    match = re.search(r"-?\d+", raw_value.strip())
                    return int(match.group(0)) if match else None
                return None

            contracts_payload: list[dict] = []
            root_alerts: list[str] = []

            if isinstance(result_payload, dict):
                root_alerts = result_payload.get("alerts", []) or []
                if isinstance(result_payload.get("contracts"), list):
                    contracts_payload = result_payload.get("contracts") or []
                else:
                    contracts_payload = [result_payload]
            elif isinstance(result_payload, list):
                contracts_payload = result_payload

            results: list[LoanContractResult] = []
            for item in contracts_payload:
                if not isinstance(item, dict):
                    continue

                item_alerts = []
                if root_alerts:
                    item_alerts.extend(root_alerts)
                item_alerts.extend(item.get("alerts", []) or [])

                results.append(
                    LoanContractResult(
                        lender_name=item.get("lenderName"),
                        contract_id=item.get("contractId"),
                        parcela_mensal=parse_field(item.get("parcelaMensal")),
                        total_parcelas=parse_int_field(item.get("totalParcelas")),
                        parcelas_pagas=parse_int_field(item.get("parcelasPagas")),
                        parcelas_restantes=parse_int_field(item.get("parcelasRestantes")),
                        valor_total=parse_field(item.get("valorTotal")),
                        taxa_juros=item.get("taxaJuros"),
                        alerts=item_alerts,
                    )
                )

            if not results:
                results.append(
                    LoanContractResult(
                        lender_name=None,
                        contract_id=None,
                        parcela_mensal=ExtractedField(None, None, None, None),
                        total_parcelas=None,
                        parcelas_pagas=None,
                        parcelas_restantes=None,
                        valor_total=ExtractedField(None, None, None, None),
                        taxa_juros=None,
                        alerts=["Nenhum contrato encontrado no extrato."],
                    )
                )

            return results
        except Exception as e:
            return [
                LoanContractResult(
                    lender_name=None,
                    contract_id=None,
                    parcela_mensal=ExtractedField(None, None, None, None),
                    total_parcelas=None,
                    parcelas_pagas=None,
                    parcelas_restantes=None,
                    valor_total=ExtractedField(None, None, None, None),
                    taxa_juros=None,
                    alerts=[f"Erro ao extrair contratos: {str(e)}"],
                )
            ]
