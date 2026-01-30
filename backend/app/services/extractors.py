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

    def _parse_brl_value(self, value_str: str) -> float | None:
        if not value_str:
            return None
        cleaned = value_str.replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _extract_inss_historico_values(self, text: str) -> dict:
        """
        Extrai valores determinísticos para Histórico de Créditos do INSS.
        """
        result: dict = {}

        # Salário bruto equivalente: rubrica 101 - VALOR TOTAL DE MR DO PERIODO
        bruto_matches = list(
            re.finditer(
                r"VALOR\s+TOTAL\s+DE\s+MR\s+DO\s+PERIODO\s*R\$\s*([\d\.]+,\d{2})",
                text,
                flags=re.IGNORECASE,
            )
        )
        if bruto_matches:
            bruto_match = bruto_matches[-1]
            bruto_value = self._parse_brl_value(bruto_match.group(1))
            if bruto_value is not None:
                result["salario_bruto"] = {
                    "value": bruto_value,
                    "evidence": bruto_match.group(0),
                }

        # Salário líquido: linha com competência + valor (ex: 12/2025 R$ 836,70)
        comp_matches = list(
            re.finditer(
                r"(\d{2}/\d{4})\s*R\$\s*([\d\.]+,\d{2})",
                text,
            )
        )
        if comp_matches:
            def comp_key(match) -> tuple[int, int]:
                mm, yyyy = match.group(1).split("/")
                return (int(yyyy), int(mm))

            comp_matches.sort(key=comp_key, reverse=True)
            best = comp_matches[0]
            liquido_value = self._parse_brl_value(best.group(2))
            if liquido_value is not None:
                result["salario_liquido"] = {
                    "value": liquido_value,
                    "evidence": best.group(0),
                    "competencia": best.group(1),
                }

        return result

    def _pick_latest_competencia(self, raw_values: list[str]) -> str | None:
        if not raw_values:
            return None

        def to_key(raw: str) -> tuple[int, int] | None:
            raw = raw.strip()
            if re.fullmatch(r"\d{4}-\d{2}", raw):
                yyyy, mm = raw.split("-")
                return (int(yyyy), int(mm))
            if re.fullmatch(r"\d{2}/\d{4}", raw):
                mm, yyyy = raw.split("/")
                return (int(yyyy), int(mm))
            return None

        candidates = []
        for raw in raw_values:
            key = to_key(raw)
            if key:
                candidates.append((key, raw))
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0], reverse=True)
        key, raw = candidates[0]
        return f"{key[0]:04d}-{key[1]:02d}"

    def _extract_inss_extrato_beneficio_values(
        self, text: str, competencias_detectadas: list[str] | None = None
    ) -> PaymentExtractionResult:
        """
        Extrai valores de benefício do Extrato de Empréstimo Consignado (INSS).
        Usa Base de Cálculo como salário bruto e Total Comprometido como descontos.
        """
        base_value = None
        base_evidence = None
        total_value = None
        total_evidence = None

        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        for i, line in enumerate(lines):
            if line.upper() in ("VALORES DO BENEFÍCIO", "VALORES DO BENEFICIO"):
                labels: list[str] = []
                values: list[str] = []

                j = i + 1
                while j < len(lines):
                    if re.match(r"R\$\s*[\d\.]+,\d{2}", lines[j]):
                        break
                    labels.append(lines[j])
                    j += 1

                while j < len(lines):
                    if re.match(r"R\$\s*[\d\.]+,\d{2}", lines[j]):
                        values.append(lines[j])
                        j += 1
                        continue
                    if values:
                        break
                    j += 1

                def normalize_label(value: str) -> str:
                    normalized = value.upper()
                    for src, dst in (
                        ("Á", "A"),
                        ("À", "A"),
                        ("Â", "A"),
                        ("Ã", "A"),
                        ("É", "E"),
                        ("Ê", "E"),
                        ("Í", "I"),
                        ("Ó", "O"),
                        ("Ô", "O"),
                        ("Õ", "O"),
                        ("Ú", "U"),
                        ("Ç", "C"),
                    ):
                        normalized = normalized.replace(src, dst)
                    return normalized

                for idx, label in enumerate(labels):
                    if idx >= len(values):
                        break
                    label_norm = normalize_label(label)
                    if base_value is None and "BASE" in label_norm and "CALCULO" in label_norm:
                        match = re.search(r"R\$\s*([\d\.]+,\d{2})", values[idx])
                        if match:
                            base_value = match.group(1)
                            base_evidence = f"{label}\\n{values[idx]}"
                    if total_value is None and "TOTAL" in label_norm and "COMPROMETIDO" in label_norm:
                        match = re.search(r"R\$\s*([\d\.]+,\d{2})", values[idx])
                        if match:
                            total_value = match.group(1)
                            total_evidence = f"{label}\\n{values[idx]}"

                # Se encontrou ao menos um dos campos, parar
                if base_value or total_value:
                    break

        if base_value is None or total_value is None:
            base_match = re.search(
                r"BASE\s+DE\s+C[ÁA]LCULO\\s*R\$\s*([\d\.]+,\d{2})",
                text,
                flags=re.IGNORECASE,
            )
            total_match = re.search(
                r"TOTAL\s+COMPROMETIDO\\s*R\$\s*([\d\.]+,\d{2})",
                text,
                flags=re.IGNORECASE,
            )
            if base_value is None and base_match:
                base_value = base_match.group(1)
                base_evidence = base_match.group(0)
            if total_value is None and total_match:
                total_value = total_match.group(1)
                total_evidence = total_match.group(0)

        competencia = None
        if competencias_detectadas:
            competencia = self._pick_latest_competencia(competencias_detectadas)
        if not competencia:
            comp_matches = re.findall(r"\b\\d{2}/\\d{4}\b", text)
            competencia = self._pick_latest_competencia(comp_matches)
        if not competencia:
            competencia = ""

        salario_bruto = ExtractedField(None, None, None, None)
        total_descontos = ExtractedField(None, None, None, None)

        if base_value:
            value = self._parse_brl_value(base_value)
            if value is not None:
                salario_bruto = ExtractedField(
                    value=value,
                    currency="BRL",
                    method="EXTRACTED_FROM_BENEFICIO_BASE",
                    evidence=FieldEvidence(page=0, text=base_evidence or ""),
                )

        if total_value:
            value = self._parse_brl_value(total_value)
            if value is not None:
                total_descontos = ExtractedField(
                    value=value,
                    currency="BRL",
                    method="EXTRACTED_FROM_TOTAL_COMPROMETIDO",
                    evidence=FieldEvidence(page=0, text=total_evidence or ""),
                )

        alerts = []
        if salario_bruto.value is None and total_descontos.value is None:
            alerts.append(
                "Valores do benefício não encontrados no extrato (base de cálculo / total comprometido)."
            )

        return PaymentExtractionResult(
            competencia=competencia,
            salario_bruto=salario_bruto,
            salario_liquido=ExtractedField(None, None, None, None),
            total_descontos=total_descontos,
            linhas_consignado=[],
            alerts=alerts,
        )

    def _extract_inss_historico_consignado_lines(
        self, text: str, competencia_mm_yyyy: str
    ) -> list[ConsignadoLine]:
        """
        Extrai linhas de consignado do Histórico de Créditos somente para a competência alvo.
        Considera apenas rubricas 216, 217 e 268.
        """
        if not competencia_mm_yyyy:
            return []

        raw_lines = [ln.strip() for ln in text.splitlines()]
        block_lines: list[str] = []

        i = 0
        while i < len(raw_lines):
            header = raw_lines[i].upper()
            if header in ("COMPETÊNCIA", "COMPETENCIA"):
                comp_line = None
                j = i + 1
                while j < len(raw_lines) and j < i + 30:
                    if re.fullmatch(r"\d{2}/\d{4}", raw_lines[j]):
                        comp_line = raw_lines[j]
                        break
                    j += 1
                if comp_line == competencia_mm_yyyy:
                    end = len(raw_lines)
                    k = i + 1
                    while k < len(raw_lines):
                        if raw_lines[k].upper() in ("COMPETÊNCIA", "COMPETENCIA"):
                            end = k
                            break
                        k += 1
                    block_lines = [ln for ln in raw_lines[i:end] if ln]
                    break
            i += 1

        if not block_lines:
            return []

        lines = block_lines
        allowed = {"216", "217", "268"}
        extracted: list[ConsignadoLine] = []

        i = 0
        while i < len(lines):
            line = lines[i]
            if re.fullmatch(r"\d{3}", line) and line in allowed:
                rubrica = line
                desc = None
                val_line = None

                j = i + 1
                while j < len(lines) and not lines[j]:
                    j += 1
                if j < len(lines):
                    desc = lines[j]

                k = j + 1
                while k < len(lines) and "R$" not in lines[k]:
                    if re.fullmatch(r"\d{3}", lines[k]):
                        break
                    k += 1
                if k < len(lines) and "R$" in lines[k]:
                    val_line = lines[k]

                if desc and val_line:
                    value = self._parse_brl_value(
                        re.sub(r".*R\$\s*", "", val_line)
                    )
                    if value is not None:
                        extracted.append(
                            ConsignadoLine(
                                descricao=desc,
                                rubrica=rubrica,
                                valor_cent=int(round(value * 100)),
                                evidence=FieldEvidence(
                                    page=0,
                                    text=f"{rubrica}\n{desc}\n{val_line}",
                                ),
                            )
                        )

                i = k + 1 if val_line else i + 1
            else:
                i += 1

        return extracted

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

        result: PaymentExtractionResult
        parse_error: Exception | None = None

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

                valor_cent = linha_dict.get("valorCent", 0)
                if valor_cent is None:
                    valor_cent = 0

                linhas.append(
                    ConsignadoLine(
                        descricao=linha_dict.get("descricao", ""),
                        rubrica=linha_dict.get("rubrica"),
                        valor_cent=valor_cent,
                        evidence=evidence,
                    )
                )

            result = PaymentExtractionResult(
                competencia=result_dict.get("competencia", ""),
                salario_bruto=parse_field(result_dict.get("salarioBruto")),
                salario_liquido=parse_field(result_dict.get("salarioLiquido")),
                total_descontos=parse_field(result_dict.get("totalDescontos")),
                linhas_consignado=linhas,
                alerts=result_dict.get("alerts", []),
            )

        except Exception as e:
            parse_error = e
            # RF-006 FE-001: Se falhar, retorna resultado vazio com alerta
            result = PaymentExtractionResult(
                competencia="",
                salario_bruto=ExtractedField(None, None, None, None),
                salario_liquido=ExtractedField(None, None, None, None),
                total_descontos=ExtractedField(None, None, None, None),
                linhas_consignado=[],
                alerts=[f"Erro ao extrair dados: {str(e)}"],
            )

        # Fallback determinístico para Histórico de Créditos INSS
        if "HISTÓRICO DE CRÉDITOS" in text.upper() or "HISTORICO DE CREDITOS" in text.upper():
            parsed = self._extract_inss_historico_values(text)
            if parsed.get("salario_bruto"):
                result.salario_bruto = ExtractedField(
                    value=parsed["salario_bruto"]["value"],
                    currency="BRL",
                    method="EXTRACTED_FROM_MR_TOTAL",
                    evidence=FieldEvidence(page=0, text=parsed["salario_bruto"]["evidence"]),
                )
            if parsed.get("salario_liquido"):
                result.salario_liquido = ExtractedField(
                    value=parsed["salario_liquido"]["value"],
                    currency="BRL",
                    method="EXTRACTED_FROM_LIQUIDO",
                    evidence=FieldEvidence(page=0, text=parsed["salario_liquido"]["evidence"]),
                )
                comp = parsed["salario_liquido"].get("competencia")
                if comp:
                    # Normaliza MM/YYYY -> YYYY-MM
                    if "/" in comp:
                        mm, yyyy = comp.split("/")
                        result.competencia = f"{yyyy}-{mm}"
                    else:
                        result.competencia = comp

                    consignado_lines = self._extract_inss_historico_consignado_lines(
                        text, comp
                    )
                    if consignado_lines:
                        result.linhas_consignado = consignado_lines

            if parse_error:
                result.alerts.append(
                    "Fallback determinístico aplicado após falha de JSON do LLM."
                )

        return result


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

    def _redact_preview(self, text: str, limit: int = 500) -> str:
        """Reduz risco de PII em previews de resposta do LLM."""
        if not text:
            return ""
        redacted = re.sub(r"\d", "X", text)
        return redacted[:limit]

    def _parse_currency_values(self, text: str) -> list[tuple[float, str]]:
        """
        Extrai valores monetários em BRL permitindo quebra de linha entre inteiro e centavos.
        Retorna lista de tuplas (valor_float, evidência_texto).
        """
        cleaned = re.sub(r"(\d,\d)\s+(\d)", r"\1\2", text or "")
        pattern = re.compile(r"R\$\s*([\d\.]+)\s*,\s*(\d{2})")
        values: list[tuple[float, str]] = []
        for match in pattern.finditer(cleaned):
            whole = match.group(1).replace(".", "")
            cents = match.group(2)
            value = float(f"{whole}.{cents}")
            values.append((value, match.group(0)))
        return values

    def _fill_missing_contract_totals(
        self, text: str, contracts: list[LoanContractResult]
    ) -> None:
        for contract in contracts:
            if contract.valor_total and contract.valor_total.value is not None:
                continue
            if not contract.contract_id:
                continue
            idx = text.find(contract.contract_id)
            if idx == -1:
                continue
            window = text[idx : idx + 800]
            currency_vals = self._parse_currency_values(window)
            if not currency_vals:
                continue
            chosen = None
            if len(currency_vals) >= 2:
                chosen = currency_vals[1]
            elif len(currency_vals) == 1 and contract.parcela_mensal.value is None:
                chosen = currency_vals[0]

            if chosen:
                contract.valor_total = ExtractedField(
                    value=chosen[0],
                    currency="BRL",
                    method="EXTRACTED_FROM_STATEMENT_REGEX",
                    evidence=FieldEvidence(page=0, text=chosen[1]),
                )
                contract.alerts.append(
                    "Valor total preenchido por fallback regex a partir do texto."
                )

    def _merge_contracts(
        self,
        primary: list[LoanContractResult],
        fallback: list[LoanContractResult],
    ) -> list[LoanContractResult]:
        by_id: dict[str, LoanContractResult] = {
            c.contract_id: c for c in primary if c.contract_id
        }
        by_parcela: dict[float, LoanContractResult] = {}
        for c in primary:
            if c.parcela_mensal.value is not None and c.valor_total.value is None:
                by_parcela[round(float(c.parcela_mensal.value), 2)] = c
        merged = list(primary)

        for fb in fallback:
            if fb.contract_id and fb.contract_id in by_id:
                base = by_id[fb.contract_id]
                if base.lender_name is None and fb.lender_name:
                    base.lender_name = fb.lender_name
                if base.parcela_mensal.value is None and fb.parcela_mensal.value is not None:
                    base.parcela_mensal = fb.parcela_mensal
                if base.valor_total.value is None and fb.valor_total.value is not None:
                    base.valor_total = fb.valor_total
                if base.total_parcelas is None and fb.total_parcelas is not None:
                    base.total_parcelas = fb.total_parcelas
                if base.parcelas_pagas is None and fb.parcelas_pagas is not None:
                    base.parcelas_pagas = fb.parcelas_pagas
                if base.parcelas_restantes is None and fb.parcelas_restantes is not None:
                    base.parcelas_restantes = fb.parcelas_restantes
                if fb.alerts:
                    base.alerts.extend(fb.alerts)
                continue

            if fb.parcela_mensal.value is not None:
                key = round(float(fb.parcela_mensal.value), 2)
                target = by_parcela.get(key)
                if target:
                    if target.valor_total.value is None and fb.valor_total.value is not None:
                        target.valor_total = fb.valor_total
                        target.alerts.append(
                            "Valor total preenchido por fallback regex (match por parcela)."
                        )
                    if target.total_parcelas is None and fb.total_parcelas is not None:
                        target.total_parcelas = fb.total_parcelas
                    if fb.alerts:
                        target.alerts.extend(fb.alerts)
                    continue

        merged.append(fb)

        # Remover possíveis IDs concatenados que contêm outros IDs válidos
        ids = [c.contract_id for c in merged if c.contract_id]
        cleaned: list[LoanContractResult] = []

        def same_values(a: LoanContractResult, b: LoanContractResult) -> bool:
            def norm(v):
                return round(float(v), 2) if v is not None else None
            return (
                norm(a.parcela_mensal.value) == norm(b.parcela_mensal.value)
                and norm(a.valor_total.value) == norm(b.valor_total.value)
                and (
                    a.total_parcelas == b.total_parcelas
                    or (a.total_parcelas is None and b.total_parcelas is None)
                )
            )

        for contract in merged:
            cid = contract.contract_id
            if not cid:
                cleaned.append(contract)
                continue
            matches = [other for other in ids if other != cid and other in cid and len(other) >= 6]
            if matches:
                # Remove IDs concatenados quando os valores são idênticos ao contrato base
                base = next((c for c in merged if c.contract_id in matches), None)
                if base and same_values(base, contract):
                    continue
            cleaned.append(contract)

        return cleaned

    def _extract_card_reserved_contracts(self, text: str) -> list[LoanContractResult]:
        """
        Extrai valores de reserva de cartão consignado (RCC/RMC) do extrato.
        Retorna como pseudo-contratos para compor consignado mensal.
        """
        results: list[LoanContractResult] = []

        pattern = re.compile(
            r"VALOR\s+LIMITE\s+DE\s+CART[ÃA]O\s+RESERVADO\s+ATUALIZADO(.*?)(?:VALORES\s+POR\s+MODALIDADE|\Z)",
            flags=re.IGNORECASE | re.DOTALL,
        )
        for match in pattern.finditer(text):
            block = match.group(0)
            values = self._parse_currency_values(block)
            if not values:
                continue
            value, evidence = min(values, key=lambda item: item[0])
            results.append(
                LoanContractResult(
                    lender_name=None,
                    contract_id=None,
                    parcela_mensal=ExtractedField(
                        value=value,
                        currency="BRL",
                        method="EXTRACTED_FROM_CARD_RESERVED",
                        evidence=FieldEvidence(page=0, text=evidence),
                    ),
                    total_parcelas=None,
                    parcelas_pagas=None,
                    parcelas_restantes=None,
                    valor_total=ExtractedField(None, None, None, None),
                    taxa_juros=None,
                    alerts=[
                        "Valor de cartão consignado (RCC/RMC) incluído no consignado mensal."
                    ],
                )
            )

        return results

    def _extract_contracts_from_text(
        self, text: str, fallback_alert: str | None
    ) -> list[LoanContractResult]:
        """
        Fallback determinístico para extratos INSS quando o LLM falha.
        Extrai contratos da seção 'EMPRÉSTIMOS BANCÁRIOS — CONTRATOS ATIVOS E SUSPENSOS'.
        """
        text_upper = text.upper()
        start_match = re.search(r"EMPR[ÉE]STIMOS\s+BANC[ÁA]RIOS", text_upper)
        if not start_match:
            return []

        start_idx = start_match.start()
        end_idx = None
        end_patterns = [
            r"CONTRATOS\s+EXCLU",
            r"CONTRATOS\s+ENCERR",
            r"CART[ÃA]O",
            r"DESCONTOS\s+DE\s+CART",
            r"RESUMO",
        ]
        for pat in end_patterns:
            m = re.search(pat, text_upper[start_idx:])
            if m:
                pos = start_idx + m.start()
                if end_idx is None or pos < end_idx:
                    end_idx = pos

        chunk = text[start_idx:end_idx] if end_idx else text[start_idx:]
        lines = [ln.strip() for ln in chunk.splitlines() if ln.strip()]

        contracts: list[LoanContractResult] = []
        current: dict[str, object] = {}
        digit_buffer = ""
        bank_name_parts: list[str] = []
        collecting_bank_name = False
        block_lines: list[str] = []

        def finalize_contract() -> None:
            nonlocal current, digit_buffer, bank_name_parts, block_lines, collecting_bank_name
            if not current and not digit_buffer:
                return
            contract_id = current.get("contract_id")
            if not contract_id and digit_buffer:
                current["contract_id"] = digit_buffer
            if bank_name_parts:
                current["lender_name"] = " ".join(bank_name_parts)

            block_text = "\n".join(block_lines)
            currency_vals = self._parse_currency_values(block_text)
            parcela_val = currency_vals[0] if len(currency_vals) > 0 else None
            total_val = currency_vals[1] if len(currency_vals) > 1 else None

            alerts = ["Extração fallback por regex (LLM inválido ou sem JSON)."]
            if fallback_alert:
                alerts.append(fallback_alert)

            parcela_field = ExtractedField(
                value=parcela_val[0] if parcela_val else None,
                currency="BRL" if parcela_val else None,
                method="EXTRACTED_FROM_STATEMENT_REGEX" if parcela_val else None,
                evidence=FieldEvidence(page=0, text=parcela_val[1]) if parcela_val else None,
            )
            total_field = ExtractedField(
                value=total_val[0] if total_val else None,
                currency="BRL" if total_val else None,
                method="EXTRACTED_FROM_STATEMENT_REGEX" if total_val else None,
                evidence=FieldEvidence(page=0, text=total_val[1]) if total_val else None,
            )

            contracts.append(
                LoanContractResult(
                    lender_name=current.get("lender_name"),
                    contract_id=current.get("contract_id"),
                    parcela_mensal=parcela_field,
                    total_parcelas=current.get("total_parcelas"),
                    parcelas_pagas=None,
                    parcelas_restantes=None,
                    valor_total=total_field,
                    taxa_juros=None,
                    alerts=alerts,
                )
            )

            current = {}
            digit_buffer = ""
            bank_name_parts = []
            block_lines = []
            collecting_bank_name = False

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
            line_upper = line_clean.upper()

            bank_line = re.search(r"\b\d{3}\s*-\s*.+", line_clean)
            if bank_line:
                if current or digit_buffer:
                    finalize_contract()
                current = {"lender_name": None, "contract_id": None, "total_parcelas": None}
                if digit_buffer:
                    current["contract_id"] = digit_buffer
                    digit_buffer = ""
                bank_name_parts = [line_clean]
                collecting_bank_name = True
                block_lines.append(line_clean)
                continue

            if collecting_bank_name:
                if (
                    re.fullmatch(r"\d{2}/\d{4}", line_clean)
                    or re.fullmatch(r"\d+", line_clean)
                    or "R$" in line_clean
                    or any(
                        kw in line_upper
                        for kw in ["ATIVO", "AVERB", "MIGRADO", "REFINAN", "SUSPENS"]
                    )
                ):
                    collecting_bank_name = False
                else:
                    bank_name_parts.append(line_clean)
                    block_lines.append(line_clean)
                    continue

            if re.fullmatch(r"\d{3,}", line_clean):
                if len(line_clean) >= 4:
                    digit_buffer += line_clean
                elif len(line_clean) == 3 and len(digit_buffer) >= 12:
                    digit_buffer += line_clean
                block_lines.append(line_clean)
                continue

            if re.fullmatch(r"\d{2}/\d{4}", line_clean):
                if "inicio" not in current:
                    current["inicio"] = line_clean
                elif "fim" not in current:
                    current["fim"] = line_clean
                block_lines.append(line_clean)
                continue

            if re.fullmatch(r"\d{2,3}", line_clean) and current is not None:
                if current.get("total_parcelas") is None:
                    current["total_parcelas"] = int(line_clean)
                block_lines.append(line_clean)
                continue

            if "ATIVO" in line_upper or "SUSPENS" in line_upper:
                block_lines.append(line_clean)
                finalize_contract()
                continue

            if current:
                block_lines.append(line_clean)

        finalize_contract()
        return contracts

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

            fallback_alert = None
            if isinstance(response, str):
                try:
                    result_payload = _safe_json_loads(response)
                except Exception:
                    fallback_alert = (
                        "Resposta do LLM inválida. Preview: "
                        + self._redact_preview(response)
                    )
                    # Retry com texto truncado e instrução explícita
                    short_prompt = self._build_loan_list_prompt(text[:8000])
                    short_prompt += "\n\nResponda SOMENTE com JSON válido, sem comentários."
                    retry_response = await _request_payload(short_prompt)
                    if isinstance(retry_response, str):
                        try:
                            result_payload = _safe_json_loads(retry_response)
                        except Exception:
                            fallback_alert = (
                                "Resposta do LLM inválida após retry. Preview: "
                                + self._redact_preview(retry_response)
                            )
                            result_payload = None
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
            elif result_payload is None:
                contracts_payload = []

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
                fallback_results = self._extract_contracts_from_text(
                    text, fallback_alert
                )
                if fallback_results:
                    return fallback_results

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

            fallback_results = self._extract_contracts_from_text(
                text, fallback_alert or "Fallback regex para completar contratos."
            )
            if fallback_results:
                results = self._merge_contracts(results, fallback_results)

            self._fill_missing_contract_totals(text, results)

            card_contracts = self._extract_card_reserved_contracts(text)
            if card_contracts:
                results.extend(card_contracts)

            return results
        except Exception as e:
            fallback_results = self._extract_contracts_from_text(
                text, f"Erro ao extrair contratos: {str(e)}"
            )
            if fallback_results:
                return fallback_results

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
