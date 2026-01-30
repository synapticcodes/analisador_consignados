"""
Router LLM Service
~~~~~~~~~~~~~~~~~~

Classifica documentos em famílias e identifica suas capabilities.
Baseado no PRD seção RF-005.
"""

from dataclasses import dataclass
from enum import Enum
import json
import re

from app.services.llm_client import LLMClient


class DocumentFamily(str, Enum):
    """Famílias de documentos suportadas (Fase 1)."""

    PAYROLL_SALARY_STATEMENT = "PAYROLL_SALARY_STATEMENT"
    INSS_HISTORICO_CREDITOS = "INSS_HISTORICO_CREDITOS"
    INSS_EXTRATO_CONSIGNADO = "INSS_EXTRATO_CONSIGNADO"
    LOAN_CONTRACT_GENERIC = "LOAN_CONTRACT_GENERIC"
    OTHER_UNKNOWN = "OTHER_UNKNOWN"


class DocumentCapability(str, Enum):
    """Capabilities que um documento pode fornecer."""

    PROVIDES_GROSS_NET_DEDUCTIONS = "PROVIDES_GROSS_NET_DEDUCTIONS"
    PROVIDES_CONSIGNADO_LINES = "PROVIDES_CONSIGNADO_LINES"
    PROVIDES_LOAN_CONTRACTS = "PROVIDES_LOAN_CONTRACTS"
    PROVIDES_COMPETENCIA_TABLE = "PROVIDES_COMPETENCIA_TABLE"


@dataclass
class RouterEvidence:
    """Evidência de classificação."""

    page: int
    text: str


@dataclass
class RouterResult:
    """Resultado da classificação do Router."""

    doc_family: str
    confidence: float
    capabilities: list[str]
    competencias_detectadas: list[str]
    evidence: list[RouterEvidence]


class RouterService:
    """Serviço de roteamento de documentos usando LLM."""

    def __init__(self, llm_client: LLMClient):
        """
        Inicializa o Router Service.

        Args:
            llm_client: Cliente LLM para comunicação com OpenAI
        """
        self.llm_client = llm_client

    def _build_router_prompt(self, text_snippet: str, metadata: dict) -> str:
        """
        Constrói o prompt do Router baseado no PRD seção 10.1.

        Args:
            text_snippet: Primeiras 3000 chars do documento
            metadata: Metadados do documento (filename, page_count, etc)

        Returns:
            Prompt formatado
        """
        return f"""Você é um classificador de documentos financeiros brasileiro especializado em folhas de pagamento e contratos de empréstimo consignado.

**TAREFA:** Analise o texto abaixo e classifique o documento em uma das famílias suportadas.

**FAMÍLIAS SUPORTADAS:**
1. PAYROLL_SALARY_STATEMENT - Folha de pagamento de servidor público ou privado
2. INSS_HISTORICO_CREDITOS - Histórico de créditos do INSS
3. INSS_EXTRATO_CONSIGNADO - Extrato de empréstimos consignados do INSS
4. LOAN_CONTRACT_GENERIC - Contrato genérico de empréstimo consignado
5. OTHER_UNKNOWN - Documento não reconhecido ou irrelevante

**CAPABILITIES (dados que o documento pode fornecer):**
- PROVIDES_GROSS_NET_DEDUCTIONS: Fornece salário bruto, líquido e descontos
- PROVIDES_CONSIGNADO_LINES: Fornece linhas de consignado detalhadas
- PROVIDES_LOAN_CONTRACTS: Fornece dados de contratos (parcela, saldo devedor, etc)
- PROVIDES_COMPETENCIA_TABLE: Fornece tabela com múltiplas competências

**REGRAS:**
1. Retorne JSON válido com a estrutura especificada
2. Confidence deve ser 0-1 (se < 0.5, use OTHER_UNKNOWN)
3. Evidence deve conter mínimo 2 trechos do texto original
4. Competências devem estar no formato YYYY-MM
5. NUNCA execute cálculos, apenas classifique

**METADADOS DO DOCUMENTO:**
- Filename: {metadata.get('filename', 'N/A')}
- Páginas: {metadata.get('page_count', 'N/A')}
- Tamanho: {metadata.get('file_size_bytes', 'N/A')} bytes

**TEXTO DO DOCUMENTO (primeiros 3000 caracteres):**
```
{text_snippet[:3000]}
```

**RESPOSTA (JSON):**
{{
  "docFamily": "PAYROLL_SALARY_STATEMENT | INSS_HISTORICO_CREDITOS | INSS_EXTRATO_CONSIGNADO | LOAN_CONTRACT_GENERIC | OTHER_UNKNOWN",
  "confidence": 0.95,
  "capabilities": ["PROVIDES_GROSS_NET_DEDUCTIONS", "PROVIDES_CONSIGNADO_LINES"],
  "competenciasDetectadas": ["2024-01", "2024-02"],
  "evidence": [
    {{"page": 0, "text": "Trecho relevante do documento que justifica a classificação"}},
    {{"page": 0, "text": "Outro trecho importante"}}
  ]
}}
"""

    async def classify_document(
        self,
        text: str,
        metadata: dict | None = None,
    ) -> RouterResult:
        """
        Classifica um documento em uma família.

        Args:
            text: Texto extraído do documento
            metadata: Metadados opcionais (filename, page_count, etc)

        Returns:
            RouterResult com classificação e evidências

        Raises:
            ValueError: Se resposta do LLM for inválida
        """
        if metadata is None:
            metadata = {}

        # Construir prompt
        text_snippet = text[:3000]  # Primeiros 3000 chars como especificado no PRD
        prompt = self._build_router_prompt(text_snippet, metadata)

        # Chamar LLM
        messages = [
            {
                "role": "system",
                "content": "Você é um classificador de documentos financeiros. Retorne apenas JSON válido.",
            },
            {"role": "user", "content": prompt},
        ]

        def _safe_json_loads(payload: str) -> dict:
            try:
                return json.loads(payload)
            except Exception:
                # Tenta extrair o primeiro objeto JSON válido dentro do texto
                start = payload.find("{")
                end = payload.rfind("}")
                if start != -1 and end != -1 and end > start:
                    return json.loads(payload[start : end + 1])
                raise

        def _find_evidence_lines(text_blob: str, patterns: list[str], limit: int = 2) -> list[RouterEvidence]:
            evidences: list[RouterEvidence] = []
            lines = text_blob.splitlines()
            for line in lines:
                line_upper = line.upper()
                if any(pat in line_upper for pat in patterns):
                    evidences.append(RouterEvidence(page=0, text=line.strip()[:200]))
                if len(evidences) >= limit:
                    break
            # Se não achou linhas suficientes, pega as primeiras linhas não vazias
            if len(evidences) < limit:
                for line in lines:
                    if line.strip():
                        evidences.append(RouterEvidence(page=0, text=line.strip()[:200]))
                    if len(evidences) >= limit:
                        break
            return evidences[:limit]

        def _heuristic_classification(text_blob: str) -> RouterResult:
            text_upper = text_blob.upper()
            # Heurísticas simples baseadas em palavras-chave
            if "FOLHA DE PAGAMENTO" in text_upper or "PROVENTOS" in text_upper and "DESCONTOS" in text_upper:
                return RouterResult(
                    doc_family=DocumentFamily.PAYROLL_SALARY_STATEMENT.value,
                    confidence=0.6,
                    capabilities=[
                        DocumentCapability.PROVIDES_GROSS_NET_DEDUCTIONS.value,
                        DocumentCapability.PROVIDES_CONSIGNADO_LINES.value,
                    ],
                    competencias_detectadas=[],
                    evidence=_find_evidence_lines(text_blob, ["FOLHA", "PROVENTOS", "DESCONTOS"]),
                )

            if "HISTÓRICO DE CRÉDITOS" in text_upper or "HISTORICO DE CREDITOS" in text_upper:
                return RouterResult(
                    doc_family=DocumentFamily.INSS_HISTORICO_CREDITOS.value,
                    confidence=0.6,
                    capabilities=[DocumentCapability.PROVIDES_GROSS_NET_DEDUCTIONS.value],
                    competencias_detectadas=[],
                    evidence=_find_evidence_lines(text_blob, ["HIST", "CRÉDITOS", "CREDITOS"]),
                )

            if (
                "EXTRATO CONSIGNADO" in text_upper
                or "CONTRATOS ATIVOS" in text_upper
                or "MARGEM CONSIGN" in text_upper
                or "VALORES POR MODALIDADE" in text_upper
            ):
                return RouterResult(
                    doc_family=DocumentFamily.INSS_EXTRATO_CONSIGNADO.value,
                    confidence=0.6,
                    capabilities=[
                        DocumentCapability.PROVIDES_CONSIGNADO_LINES.value,
                        DocumentCapability.PROVIDES_LOAN_CONTRACTS.value,
                    ],
                    competencias_detectadas=[],
                    evidence=_find_evidence_lines(text_blob, ["EXTRATO", "CONTRATOS", "MARGEM", "MODALIDADE"]),
                )

            if "CONTRATO" in text_upper and ("EMPRÉSTIMO" in text_upper or "EMPRESTIMO" in text_upper):
                return RouterResult(
                    doc_family=DocumentFamily.LOAN_CONTRACT_GENERIC.value,
                    confidence=0.6,
                    capabilities=[DocumentCapability.PROVIDES_LOAN_CONTRACTS.value],
                    competencias_detectadas=[],
                    evidence=_find_evidence_lines(text_blob, ["CONTRATO", "EMPRÉSTIMO", "EMPRESTIMO"]),
                )

            return RouterResult(
                doc_family=DocumentFamily.OTHER_UNKNOWN.value,
                confidence=0.3,
                capabilities=[],
                competencias_detectadas=[],
                evidence=_find_evidence_lines(text_blob, ["DOCUMENTO"]),
            )

        try:
            # Chamar com retry (RF-005 FE-001)
            response = await self.llm_client.chat_completion_with_retry(
                messages=messages, max_retries=1
            )

            # Parse response
            if isinstance(response, str):
                result_dict = _safe_json_loads(response)
            else:
                result_dict = response

            # Validar confidence (RF-005 CA-004)
            confidence = result_dict.get("confidence", 0.0)
            doc_family = result_dict.get("docFamily", "OTHER_UNKNOWN")

            if confidence < 0.5:
                doc_family = "OTHER_UNKNOWN"

            # Extrair evidence
            evidence_list = []
            for ev in result_dict.get("evidence", []):
                evidence_list.append(
                    RouterEvidence(page=ev.get("page", 0), text=ev.get("text", "")[:200])
                )

            # Se confiança baixa, aplicar heurística
            if confidence < 0.5 or doc_family == DocumentFamily.OTHER_UNKNOWN.value:
                return _heuristic_classification(text)

            return RouterResult(
                doc_family=doc_family,
                confidence=confidence,
                capabilities=result_dict.get("capabilities", []),
                competencias_detectadas=result_dict.get("competenciasDetectadas", []),
                evidence=evidence_list if evidence_list else _find_evidence_lines(text, []),
            )

        except Exception as e:
            # RF-005 FE-001: Se falhar, tenta heurística determinística
            return _heuristic_classification(text)

    def to_dict(self, result: RouterResult) -> dict:
        """
        Converte RouterResult para dict (para persistir em DB).

        Args:
            result: Resultado do router

        Returns:
            Dicionário com dados serializáveis
        """
        return {
            "docFamily": result.doc_family,
            "confidence": result.confidence,
            "capabilities": result.capabilities,
            "competenciasDetectadas": result.competencias_detectadas,
            "evidence": [
                {"page": ev.page, "text": ev.text} for ev in result.evidence
            ],
        }
