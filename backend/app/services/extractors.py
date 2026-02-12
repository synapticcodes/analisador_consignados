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
    descricao_raw: str | None = None
    descricao_canonica: str | None = None


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
    status: str | None = None
    cet_mensal: str | None = None
    cet_anual: str | None = None
    iof_cent: int | None = None
    valor_emprestado_cent: int | None = None


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

    def _normalize_for_match(self, value: str) -> str:
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

    def _canonicalize_consignado_desc(self, value: str | None) -> str:
        """Normaliza descrição para comparação e agrupamento, sem perder o texto bruto."""
        if not value:
            return ""
        collapsed = re.sub(r"\s+", " ", value).strip()
        return collapsed.upper()

    def _extract_brl_from_line(self, line: str) -> float | None:
        match = re.search(
            r"(?:R\$\s*)?(-?\d{1,3}(?:\.\d{3})*,\d{2})", line
        )
        if not match:
            return None
        return self._parse_brl_value(match.group(1))

    def _is_consignado_desc(self, line: str) -> bool:
        normalized = self._normalize_for_match(line)
        has_keyword = "EMPREST" in normalized or "AMORT" in normalized
        if not has_keyword:
            return False
        if "IRRF" in normalized or re.search(r"\bIR\b", normalized):
            return False
        excludes = ("PREVID", "PREV", "SINDIC", "SIND")
        return not any(token in normalized for token in excludes)

    def _is_descontos_header(self, line: str) -> bool:
        normalized = self._normalize_for_match(line)
        return "DESCONTOS" in normalized and "TOTAL" not in normalized

    def _is_descontos_terminator(self, line: str) -> bool:
        normalized = self._normalize_for_match(line)
        if "TOTAL" in normalized and "DESCONTO" in normalized:
            return True
        if "TOTAL" in normalized and "PROVENTO" in normalized:
            return True
        if "LIQUIDO" in normalized:
            return True
        if "BRUTO" in normalized:
            return True
        if "PROVENTOS" in normalized or "VANTAGENS" in normalized:
            return True
        if "RESUMO" in normalized or "BASE" in normalized:
            return True
        return False

    def _extract_payroll_consignado_lines_deterministic(
        self, text: str
    ) -> list[ConsignadoLine]:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        blocks: list[list[str]] = []

        i = 0
        while i < len(lines):
            if self._is_descontos_header(lines[i]):
                start = i + 1
                end = start
                while end < len(lines) and not self._is_descontos_terminator(lines[end]):
                    end += 1
                if start < end:
                    blocks.append(lines[start:end])
                i = end
                continue
            i += 1

        extracted: list[ConsignadoLine] = []
        for block in blocks:
            i = 0
            pending: dict[str, str | float | None] | None = None
            while i < len(block):
                line = block[i]
                if re.fullmatch(r"\d{3}", line):
                    pending = {
                        "rubrica": line,
                        "value": None,
                        "value_line": None,
                        "desc": None,
                        "desc_line": None,
                    }
                    i += 1
                    continue

                value = self._extract_brl_from_line(line)
                is_desc = self._is_consignado_desc(line)

                if pending:
                    if is_desc and pending["desc"] is None:
                        pending["desc"] = line
                        pending["desc_line"] = line
                    if value is not None and pending["value"] is None:
                        pending["value"] = value
                        pending["value_line"] = line
                    if pending["desc"] and pending["value"] is not None:
                        valor_cent = int(round(float(pending["value"]) * 100))
                        evidence_text = "\n".join(
                            part
                            for part in (
                                pending["rubrica"],
                                pending["value_line"],
                                pending["desc_line"],
                            )
                            if part
                        )
                        extracted.append(
                            ConsignadoLine(
                                descricao=str(pending["desc"]),
                                rubrica=str(pending["rubrica"]),
                                valor_cent=valor_cent,
                                evidence=FieldEvidence(page=0, text=evidence_text),
                                descricao_raw=str(pending["desc"]),
                                descricao_canonica=self._canonicalize_consignado_desc(
                                    str(pending["desc"])
                                ),
                            )
                        )
                        pending = None
                    i += 1
                    continue

                if is_desc:
                    if value is not None:
                        extracted.append(
                            ConsignadoLine(
                                descricao=line,
                                rubrica=None,
                                valor_cent=int(round(value * 100)),
                                evidence=FieldEvidence(page=0, text=line),
                                descricao_raw=line,
                                descricao_canonica=self._canonicalize_consignado_desc(line),
                            )
                        )
                        i += 1
                        continue
                    if i + 1 < len(block):
                        next_value = self._extract_brl_from_line(block[i + 1])
                        if next_value is not None:
                            evidence_text = f"{line}\n{block[i + 1]}"
                            extracted.append(
                                ConsignadoLine(
                                    descricao=line,
                                    rubrica=None,
                                    valor_cent=int(round(next_value * 100)),
                                    evidence=FieldEvidence(page=0, text=evidence_text),
                                    descricao_raw=line,
                                    descricao_canonica=self._canonicalize_consignado_desc(
                                        line
                                    ),
                                )
                            )
                            i += 2
                            continue

                if value is not None and i + 1 < len(block):
                    next_line = block[i + 1]
                    if self._is_consignado_desc(next_line):
                        evidence_text = f"{next_line}\n{line}"
                        extracted.append(
                            ConsignadoLine(
                                descricao=next_line,
                                rubrica=None,
                                valor_cent=int(round(value * 100)),
                                evidence=FieldEvidence(page=0, text=evidence_text),
                                descricao_raw=next_line,
                                descricao_canonica=self._canonicalize_consignado_desc(
                                    next_line
                                ),
                            )
                        )
                        i += 2
                        continue

                i += 1

        return extracted

    def _is_probably_payroll_text(self, text: str) -> bool:
        normalized = self._normalize_for_match(text or "")
        checks = [
            "FOLHA",
            "COMPROVANTE DE RENDIMENTOS",
            "PROVENTOS",
            "RENDIMENTOS",
            "DESCONTOS",
            "LIQUIDO",
        ]
        hits = sum(1 for token in checks if token in normalized)
        return hits >= 2 and "DESCONT" in normalized

    def _extract_payroll_summary_values_deterministic(
        self, text: str
    ) -> dict[str, tuple[float, str]]:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        results: dict[str, tuple[float, str]] = {}

        label_patterns: dict[str, tuple[str, ...]] = {
            "salario_bruto": (
                r"\bSAL[ÁA]RIO\s+BRUTO\b",
                r"\bTOTAL\s+DE?\s*PROVENTOS\b",
                r"\bBRUTO\b",
            ),
            "salario_liquido": (
                r"\bL[ÍI]QUIDO\s+A\s+RECEBER\b",
                r"\bSAL[ÁA]RIO\s+L[ÍI]QUIDO\b",
                r"\bL[ÍI]QUIDO\b",
            ),
            "total_descontos": (
                r"\bTOTAL\s+DE?\s*DESCONTOS\b",
                r"\bTOTAL\s+DESCONTOS\b",
                r"\bDESCONTO[S]?\b",
            ),
        }

        def line_has_any_label(raw_line: str) -> bool:
            norm = self._normalize_for_match(raw_line)
            for patterns in label_patterns.values():
                if any(re.search(pat, norm, flags=re.IGNORECASE) for pat in patterns):
                    return True
            return False

        def matches_field(field: str, raw_line: str) -> bool:
            norm = self._normalize_for_match(raw_line)
            patterns = label_patterns[field]
            return any(re.search(pat, norm, flags=re.IGNORECASE) for pat in patterns)

        for idx, line in enumerate(lines):
            if len(results) == len(label_patterns):
                break

            for field in label_patterns:
                if field in results:
                    continue
                if not matches_field(field, line):
                    continue

                same_line = self._extract_brl_from_line(line)
                if same_line is not None:
                    results[field] = (same_line, line)
                    continue

                for offset in range(1, 4):
                    j = idx + offset
                    if j >= len(lines):
                        break
                    probe = lines[j]
                    if line_has_any_label(probe):
                        break
                    value = self._extract_brl_from_line(probe)
                    if value is None:
                        continue
                    results[field] = (value, f"{line}\n{probe}")
                    break

        return results

    def _merge_consignado_lines(
        self,
        existing: list[ConsignadoLine],
        incoming: list[ConsignadoLine],
    ) -> tuple[list[ConsignadoLine], int]:
        merged = list(existing)
        existing_keys = {
            (
                self._normalize_for_match(
                    line.descricao_canonica or line.descricao or ""
                ),
                line.valor_cent,
                line.rubrica or "",
            )
            for line in existing
        }
        added = 0
        for line in incoming:
            key = (
                self._normalize_for_match(
                    line.descricao_canonica or line.descricao or ""
                ),
                line.valor_cent,
                line.rubrica or "",
            )
            if key in existing_keys:
                continue
            merged.append(line)
            existing_keys.add(key)
            added += 1
        return merged, added

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
                                descricao_raw=desc,
                                descricao_canonica=self._canonicalize_consignado_desc(desc),
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
                descricao = linha_dict.get("descricao", "")
                descricao_raw = (
                    linha_dict.get("descricao_raw")
                    or linha_dict.get("descricaoRaw")
                    or descricao
                )
                descricao_canonica = (
                    linha_dict.get("descricao_canonica")
                    or linha_dict.get("descricaoCanonica")
                    or self._canonicalize_consignado_desc(descricao)
                )

                valor_cent = linha_dict.get("valorCent", 0)
                if valor_cent is None:
                    valor_cent = 0

                linhas.append(
                    ConsignadoLine(
                        descricao=descricao,
                        rubrica=linha_dict.get("rubrica"),
                        valor_cent=valor_cent,
                        evidence=evidence,
                        descricao_raw=descricao_raw,
                        descricao_canonica=descricao_canonica,
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

        # Complemento deterministico: linhas de consignado em DESCONTOS
        deterministic_lines = self._extract_payroll_consignado_lines_deterministic(text)
        if deterministic_lines:
            merged, added = self._merge_consignado_lines(
                result.linhas_consignado, deterministic_lines
            )
            if added:
                result.linhas_consignado = merged
                result.alerts.append(
                    "Consignado complementado por regra deterministica."
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

        # Fallback determinístico para folha/contracheque (quando LLM falha ou retorna campos incompletos)
        if self._is_probably_payroll_text(text):
            summary_values = self._extract_payroll_summary_values_deterministic(text)
            applied_fields = 0

            if (
                result.salario_bruto.value is None
                and summary_values.get("salario_bruto") is not None
            ):
                value, evidence_text = summary_values["salario_bruto"]
                result.salario_bruto = ExtractedField(
                    value=value,
                    currency="BRL",
                    method="EXTRACTED_FROM_BRUTO_SUMMARY",
                    evidence=FieldEvidence(page=0, text=evidence_text),
                )
                applied_fields += 1

            if (
                result.salario_liquido.value is None
                and summary_values.get("salario_liquido") is not None
            ):
                value, evidence_text = summary_values["salario_liquido"]
                result.salario_liquido = ExtractedField(
                    value=value,
                    currency="BRL",
                    method="EXTRACTED_FROM_LIQUIDO_SUMMARY",
                    evidence=FieldEvidence(page=0, text=evidence_text),
                )
                applied_fields += 1

            if (
                result.total_descontos.value is None
                and summary_values.get("total_descontos") is not None
            ):
                value, evidence_text = summary_values["total_descontos"]
                result.total_descontos = ExtractedField(
                    value=value,
                    currency="BRL",
                    method="EXTRACTED_FROM_DESCONTOS_SUMMARY",
                    evidence=FieldEvidence(page=0, text=evidence_text),
                )
                applied_fields += 1

            if parse_error and applied_fields:
                result.alerts.append(
                    "Fallback determinístico aplicado para resumo de contracheque."
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

            def parse_cent_field(raw_value) -> int | None:
                if raw_value is None:
                    return None
                if isinstance(raw_value, dict):
                    if raw_value.get("value") is not None:
                        try:
                            return int(round(float(raw_value.get("value")) * 100))
                        except (TypeError, ValueError):
                            return None
                    raw_value = raw_value.get("cent")
                if isinstance(raw_value, (int, float)):
                    return int(round(float(raw_value)))
                if isinstance(raw_value, str):
                    return self._parse_brl_to_cent(raw_value)
                return None

            def parse_cent_field(raw_value) -> int | None:
                if raw_value is None:
                    return None
                if isinstance(raw_value, dict):
                    if raw_value.get("value") is not None:
                        try:
                            return int(round(float(raw_value.get("value")) * 100))
                        except (TypeError, ValueError):
                            return None
                    raw_value = raw_value.get("cent")
                if isinstance(raw_value, (int, float)):
                    return int(round(float(raw_value)))
                if isinstance(raw_value, str):
                    return self._parse_brl_to_cent(raw_value)
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
                status=result_dict.get("status"),
                cet_mensal=result_dict.get("cetMensal"),
                cet_anual=result_dict.get("cetAnual"),
                iof_cent=parse_cent_field(result_dict.get("iof")),
                valor_emprestado_cent=parse_cent_field(
                    result_dict.get("valorEmprestado")
                ),
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
                status=None,
            )

    def _redact_preview(self, text: str, limit: int = 500) -> str:
        """Reduz risco de PII em previews de resposta do LLM."""
        if not text:
            return ""
        redacted = re.sub(r"\d", "X", text)
        return redacted[:limit]

    def _normalize_for_match(self, value: str) -> str:
        normalized = (value or "").upper()
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
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _parse_currency_values(self, text: str) -> list[tuple[float, str]]:
        """
        Extrai valores monetários em BRL permitindo quebra de linha entre inteiro e centavos.
        Retorna lista de tuplas (valor_float, evidência_texto).
        """
        cleaned = re.sub(r"(?<=\d)\s+(?=\d)", "", text or "")
        pattern = re.compile(r"R\$\s*([\d\.]+)\s*,\s*(\d{2})")
        values: list[tuple[float, str]] = []
        for match in pattern.finditer(cleaned):
            whole = match.group(1).replace(".", "")
            cents = match.group(2)
            value = float(f"{whole}.{cents}")
            values.append((value, match.group(0)))
        return values

    def _parse_currency_values_strict(self, text: str) -> list[tuple[float, str]]:
        """
        Extrai valores monetários em BRL sem concatenar dígitos separados por espaço.
        Usado em modo rígido para evitar interpretações indevidas em tabelas quebradas.
        """
        pattern = re.compile(r"R\$\s*([\d\.]+)\s*,\s*(\d{2})")
        values: list[tuple[float, str]] = []
        for match in pattern.finditer(text or ""):
            whole = match.group(1).replace(".", "")
            cents = match.group(2)
            value = float(f"{whole}.{cents}")
            values.append((value, match.group(0)))
        return values

    def _parse_brl_to_cent(self, value: str | None) -> int | None:
        if not value:
            return None
        cleaned = value.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
        try:
            return int(round(float(cleaned) * 100))
        except ValueError:
            return None

    def _extract_brl_from_line(self, line: str) -> float | None:
        match = re.search(r"(?:R\$\s*)?(-?\d{1,3}(?:\.\d{3})*,\d{2})", line or "")
        if not match:
            return None
        parsed = self._parse_brl_to_cent(match.group(1))
        if parsed is None:
            return None
        return parsed / 100

    def _extract_percentage(self, text: str, label: str) -> str | None:
        pattern = re.compile(
            rf"{label}\s*[:\-]?\s*(\d{{1,2}},\d{{1,2}}%)",
            flags=re.IGNORECASE,
        )
        match = pattern.search(text)
        return match.group(1) if match else None

    def _normalize_rate_value(self, value: str | None) -> str | None:
        if value is None:
            return None
        candidate = str(value).strip()
        if not candidate:
            return None
        compact = candidate.replace(" ", "")
        match = re.fullmatch(r"(\d{1,2},\d{1,2})%?", compact)
        if match:
            return f"{match.group(1)}%"
        return candidate

    def extract_inss_margin_data(self, text: str) -> dict[str, object] | None:
        """
        Extrai dados de margem do extrato INSS.
        Retorna None quando não encontra base suficiente para montar a seção.
        """
        normalized = re.sub(r"\s+", " ", text or "")

        def capture_brl(label: str) -> tuple[int | None, str | None]:
            pattern = re.compile(
                rf"{label}\s*[:\-]?\s*R\$\s*([\d\.]+,\d{{2}})",
                flags=re.IGNORECASE,
            )
            match = pattern.search(normalized)
            if not match:
                return None, None
            return self._parse_brl_to_cent(match.group(1)), match.group(0)

        def capture_benefit_values_vertical_layout() -> dict[str, int | str | None]:
            section_match = re.search(
                r"VALORES\s+DO\s+BENEF[ÍI]CIO(.*?)(?:\n\s*\d+\s*/\s*\d+|\Z)",
                text or "",
                flags=re.IGNORECASE | re.DOTALL,
            )
            if not section_match:
                return {
                    "base_calculo_cent": None,
                    "max_comprometimento_cent": None,
                    "total_comprometido_cent": None,
                    "base_evidence": None,
                    "max_evidence": None,
                    "total_evidence": None,
                }

            section_text = section_match.group(1)
            currency_matches = re.findall(
                r"R\$\s*([\d\.]+,\d{2})", section_text, flags=re.IGNORECASE
            )
            parsed_values = [
                self._parse_brl_to_cent(match)
                for match in currency_matches
                if self._parse_brl_to_cent(match) is not None
            ]
            if len(parsed_values) < 3:
                return {
                    "base_calculo_cent": None,
                    "max_comprometimento_cent": None,
                    "total_comprometido_cent": None,
                    "base_evidence": None,
                    "max_evidence": None,
                    "total_evidence": None,
                }

            base_cent = parsed_values[0]
            second_cent = parsed_values[1]
            third_cent = parsed_values[2]
            max_cent = max(second_cent, third_cent)
            total_cent = min(second_cent, third_cent)

            return {
                "base_calculo_cent": base_cent,
                "max_comprometimento_cent": max_cent,
                "total_comprometido_cent": total_cent,
                "base_evidence": f"VALORES DO BENEFÍCIO ... R$ {currency_matches[0]}",
                "max_evidence": (
                    "VALORES DO BENEFÍCIO (layout vertical): "
                    "MÁXIMO/TOTAL mapeados por consistência numérica"
                ),
                "total_evidence": (
                    "VALORES DO BENEFÍCIO (layout vertical): "
                    "MÁXIMO/TOTAL mapeados por consistência numérica"
                ),
            }

        def capture_modalidade_available_margins() -> dict[str, int | str | None]:
            section_match = re.search(
                r"Margem\s+para\s+Empr[ée]stimo/Cart[ãa]o\s+e\s+Resumo\s+Financeiro(.*?)(?:VALORES\s+POR\s+MODALIDADE|\Z)",
                text or "",
                flags=re.IGNORECASE | re.DOTALL,
            )
            if not section_match:
                return {
                    "margem_emprestimo_cent": None,
                    "margem_rmc_cent": None,
                    "margem_rcc_cent": None,
                    "margem_emprestimo_evidence": None,
                    "margem_rmc_evidence": None,
                    "margem_rcc_evidence": None,
                }

            section_text = section_match.group(1)
            lines = [ln.strip() for ln in section_text.splitlines() if ln.strip()]

            def currencies_in_line(line: str) -> list[int]:
                values: list[int] = []
                for token in re.findall(r"R\$\s*([\d\.]+,\d{2})", line, flags=re.IGNORECASE):
                    parsed = self._parse_brl_to_cent(token)
                    if parsed is not None:
                        values.append(parsed)
                return values

            margem_emprestimo_cent = None
            margem_emprestimo_evidence = None
            values_in_order: list[int] = []
            for ln in lines:
                values_in_order.extend(currencies_in_line(ln))

            for idx in range(len(values_in_order) - 2):
                a, b, c = values_in_order[idx], values_in_order[idx + 1], values_in_order[idx + 2]
                if a > 0 and abs(a - (b + c)) <= 1:
                    margem_emprestimo_cent = min(b, c)
                    margem_emprestimo_evidence = (
                        "VALORES POR MODALIDADE (layout em colunas): "
                        "margem empréstimo inferida por identidade consignável=utilizada+disponível"
                    )
                    break

            total_disponivel_cent = None
            if (
                max_comprometimento_cent is not None
                and total_comprometido_cent is not None
                and max_comprometimento_cent >= total_comprometido_cent
            ):
                total_disponivel_cent = (
                    max_comprometimento_cent - total_comprometido_cent
                )

            remaining_modal_cent = None
            if (
                total_disponivel_cent is not None
                and margem_emprestimo_cent is not None
                and total_disponivel_cent >= margem_emprestimo_cent
            ):
                remaining_modal_cent = total_disponivel_cent - margem_emprestimo_cent

            margem_rcc_cent = None
            margem_rmc_cent = None
            margem_rcc_evidence = None
            margem_rmc_evidence = None

            rcc_idx = next(
                (
                    idx
                    for idx, ln in enumerate(lines)
                    if "RCC" in self._normalize_for_match(ln)
                ),
                None,
            )
            rcc_window_values: list[int] = []
            if rcc_idx is not None:
                for ln in lines[rcc_idx + 1 : rcc_idx + 10]:
                    rcc_window_values.extend(currencies_in_line(ln))

            if remaining_modal_cent is not None:
                if remaining_modal_cent > 0:
                    if remaining_modal_cent in rcc_window_values:
                        margem_rcc_cent = remaining_modal_cent
                    elif rcc_window_values:
                        candidates = [v for v in rcc_window_values if 0 <= v <= remaining_modal_cent]
                        if candidates:
                            margem_rcc_cent = max(candidates)
                        else:
                            margem_rcc_cent = remaining_modal_cent
                    else:
                        margem_rcc_cent = remaining_modal_cent
                else:
                    margem_rcc_cent = 0

                if margem_rcc_cent is not None:
                    margem_rmc_cent = max(remaining_modal_cent - margem_rcc_cent, 0)
                    margem_rcc_evidence = (
                        "VALORES POR MODALIDADE (layout em colunas): "
                        "margem RCC inferida pela coluna RCC e reconciliação com máximo-comprometido"
                    )
                    margem_rmc_evidence = (
                        "VALORES POR MODALIDADE (layout em colunas): "
                        "margem RMC inferida por reconciliação com máximo-comprometido"
                    )

            return {
                "margem_emprestimo_cent": margem_emprestimo_cent,
                "margem_rmc_cent": margem_rmc_cent,
                "margem_rcc_cent": margem_rcc_cent,
                "margem_emprestimo_evidence": margem_emprestimo_evidence,
                "margem_rmc_evidence": margem_rmc_evidence,
                "margem_rcc_evidence": margem_rcc_evidence,
            }

        base_calculo_cent, base_evidence = capture_brl(r"BASE\s+DE\s+C[ÁA]LCULO")
        max_comprometimento_cent, max_evidence = capture_brl(
            r"M[ÁA]XIMO\s+DE\s+COMPROMETIMENTO"
        )
        total_comprometido_cent, total_evidence = capture_brl(
            r"TOTAL\s+COMPROMETIDO"
        )

        if (
            base_calculo_cent is None
            or max_comprometimento_cent is None
            or total_comprometido_cent is None
        ):
            vertical_values = capture_benefit_values_vertical_layout()
            if base_calculo_cent is None:
                base_calculo_cent = vertical_values["base_calculo_cent"]
                base_evidence = vertical_values["base_evidence"]
            if max_comprometimento_cent is None:
                max_comprometimento_cent = vertical_values["max_comprometimento_cent"]
                max_evidence = vertical_values["max_evidence"]
            if total_comprometido_cent is None:
                total_comprometido_cent = vertical_values["total_comprometido_cent"]
                total_evidence = vertical_values["total_evidence"]

        margem_emprestimo_cent, margem_emprestimo_evidence = capture_brl(
            r"MARGEM\s+DISPON[ÍI]VEL\s*[—-]?\s*EMPR[ÉE]STIMO"
        )
        margem_rmc_cent, margem_rmc_evidence = capture_brl(
            r"MARGEM\s+DISPON[ÍI]VEL\s*[—-]?\s*RMC"
        )
        margem_rcc_cent, margem_rcc_evidence = capture_brl(
            r"MARGEM\s+DISPON[ÍI]VEL\s*[—-]?\s*RCC"
        )

        if (
            margem_emprestimo_cent is None
            or margem_rmc_cent is None
            or margem_rcc_cent is None
        ):
            modalidade_values = capture_modalidade_available_margins()
            if margem_emprestimo_cent is None:
                margem_emprestimo_cent = modalidade_values["margem_emprestimo_cent"]
                margem_emprestimo_evidence = modalidade_values["margem_emprestimo_evidence"]
            if margem_rmc_cent is None:
                margem_rmc_cent = modalidade_values["margem_rmc_cent"]
                margem_rmc_evidence = modalidade_values["margem_rmc_evidence"]
            if margem_rcc_cent is None:
                margem_rcc_cent = modalidade_values["margem_rcc_cent"]
                margem_rcc_evidence = modalidade_values["margem_rcc_evidence"]

        cet_mensal = self._extract_percentage(normalized, r"CET\s+MENSAL")
        cet_anual = self._extract_percentage(normalized, r"CET\s+ANUAL")

        rmc_details = self._extract_inss_rmc_details(normalized)

        has_any_margin_data = any(
            value is not None
            for value in (
                base_calculo_cent,
                max_comprometimento_cent,
                total_comprometido_cent,
                margem_emprestimo_cent,
                margem_rmc_cent,
                margem_rcc_cent,
                cet_mensal,
                cet_anual,
                rmc_details.get("rmc_banco"),
                rmc_details.get("rmc_limite_cent"),
                rmc_details.get("rmc_reservado_cent"),
            )
        )
        if not has_any_margin_data:
            return None

        evidence = {
            "base_calculo": base_evidence,
            "max_comprometimento": max_evidence,
            "total_comprometido": total_evidence,
            "margem_emprestimo": margem_emprestimo_evidence,
            "margem_rmc": margem_rmc_evidence,
            "margem_rcc": margem_rcc_evidence,
        }

        return {
            "base_calculo_cent": base_calculo_cent,
            "max_comprometimento_cent": max_comprometimento_cent,
            "total_comprometido_cent": total_comprometido_cent,
            "margem_emprestimo_cent": margem_emprestimo_cent,
            "margem_rmc_cent": margem_rmc_cent,
            "margem_rcc_cent": margem_rcc_cent,
            "cet_mensal": cet_mensal,
            "cet_anual": cet_anual,
            "rmc_banco": rmc_details.get("rmc_banco"),
            "rmc_limite_cent": rmc_details.get("rmc_limite_cent"),
            "rmc_reservado_cent": rmc_details.get("rmc_reservado_cent"),
            "evidence": evidence,
        }

    def _extract_inss_rmc_details(self, text: str) -> dict[str, object]:
        """Extrai detalhes de cartão RMC/RCC quando presentes."""
        result: dict[str, object] = {
            "rmc_banco": None,
            "rmc_limite_cent": None,
            "rmc_reservado_cent": None,
        }

        banco_match = re.search(
            r"CART[ÃA]O\s+DE\s+CR[ÉE]DITO.*?(?:BANCO|BANC)\s*[:\-]?\s*([A-Z0-9\s\-\.]{3,80}?)(?=\s+(?:LIMITE|RESERVADO|R\$)|$)",
            text,
            flags=re.IGNORECASE,
        )
        if banco_match:
            result["rmc_banco"] = banco_match.group(1).strip()

        limite_match = re.search(
            r"LIMITE\s*[:\-]?\s*R\$\s*([\d\.]+,\d{2})",
            text,
            flags=re.IGNORECASE,
        )
        if limite_match:
            result["rmc_limite_cent"] = self._parse_brl_to_cent(limite_match.group(1))

        reservado_match = re.search(
            r"(?:RESERVADO|RESERVA(?:\s+DE)?\s+MARGEM)\s*[:\-]?\s*R\$\s*([\d\.]+,\d{2})",
            text,
            flags=re.IGNORECASE,
        )
        if reservado_match:
            result["rmc_reservado_cent"] = self._parse_brl_to_cent(
                reservado_match.group(1)
            )

        # Fallback para layout tabular do INSS (página "CARTÃO DE CRÉDITO - RMC",
        # seção "CONTRATOS ATIVOS E SUSPENSOS"), onde o "reservado" aparece
        # como segunda moeda da linha, antes do texto "Reserva de Margem...".
        if (
            result["rmc_banco"] is None
            or result["rmc_limite_cent"] is None
            or result["rmc_reservado_cent"] is None
        ):
            active_section_match = re.search(
                r"CART[ÃA]O\s+DE\s+CR[ÉE]DITO\s*-\s*RMC.*?CONTRATOS\s+ATIVOS\s+E\s+SUSPENSOS\*?(.*?)(?:\*Contratos\s+que\s+comprometem|CONTRATOS\s+EXCLU[ÍI]DOS|DESCONTOS\s+DE\s+CART[ÃA]O|\Z)",
                text,
                flags=re.IGNORECASE | re.DOTALL,
            )
            if active_section_match:
                active_section = active_section_match.group(1)

                if result["rmc_banco"] is None:
                    bank_row_match = re.search(
                        r"(\d{3}\s*-\s*BANCO[ A-Z0-9\-\.\n]{2,120}?)(?=\s+R\$\s*[\d\.]+,\d{2})",
                        active_section,
                        flags=re.IGNORECASE | re.DOTALL,
                    )
                    if bank_row_match:
                        result["rmc_banco"] = re.sub(
                            r"\s+",
                            " ",
                            bank_row_match.group(1).strip(),
                        )

                values_in_section = re.findall(
                    r"R\$\s*([\d\.]+,\d{2})",
                    active_section,
                    flags=re.IGNORECASE,
                )
                parsed_values = [
                    self._parse_brl_to_cent(value)
                    for value in values_in_section
                    if self._parse_brl_to_cent(value) is not None
                ]
                if parsed_values:
                    if result["rmc_limite_cent"] is None:
                        result["rmc_limite_cent"] = parsed_values[0]
                    if result["rmc_reservado_cent"] is None and len(parsed_values) > 1:
                        result["rmc_reservado_cent"] = parsed_values[1]

        return result

    def _parse_date_br(self, value: str | None) -> str | None:
        if not value:
            return None
        match = re.match(r"(\d{2})/(\d{2})/(\d{4})", value.strip())
        if not match:
            return None
        dd, mm, yyyy = match.groups()
        return f"{yyyy}-{mm}-{dd}"

    def extract_inss_historical_contracts(self, text: str) -> list[dict[str, object]]:
        """
        Extrai contratos da seção de encerrados/excluídos do extrato INSS.
        """
        section = re.search(
            r"CONTRATOS\s+EXCLU[ÍI]DOS\s+E\s+ENCERRADOS(.*?)(?:CART[ÃA]O\s+DE\s+CR[ÉE]DITO|\Z)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not section:
            return []

        lines = [ln.strip() for ln in section.group(1).splitlines() if ln.strip()]
        contracts: list[dict[str, object]] = []
        current: dict[str, object] = {}

        def flush_current() -> None:
            nonlocal current
            if not current:
                return
            contracts.append(current)
            current = {}

        for line in lines:
            if re.search(r"\b\d{3}\s*-\s*[A-Z]", line):
                flush_current()
                current["lender_name"] = line
                continue

            if "CONTRAT" in line.upper():
                contract_match = re.search(r"(\d{6,})", line)
                if contract_match:
                    current["contract_id"] = contract_match.group(1)
                continue

            date_matches = re.findall(r"\d{2}/\d{2}/\d{4}", line)
            if date_matches:
                if "data_contratacao" not in current:
                    current["data_contratacao"] = self._parse_date_br(date_matches[0])
                if len(date_matches) > 1:
                    current["data_quitacao"] = self._parse_date_br(date_matches[1])
                continue

            parcela_match = re.search(r"PARCELA.*?R\$\s*([\d\.]+,\d{2})", line, re.IGNORECASE)
            if parcela_match:
                current["parcela_cent"] = self._parse_brl_to_cent(parcela_match.group(1))
                continue

            emprestado_match = re.search(
                r"(?:VALOR\s+EMPRESTADO|VALOR\s+LIBERADO).*?R\$\s*([\d\.]+,\d{2})",
                line,
                re.IGNORECASE,
            )
            if emprestado_match:
                current["valor_emprestado_cent"] = self._parse_brl_to_cent(
                    emprestado_match.group(1)
                )
                continue

            if any(token in line.upper() for token in ("ENCERR", "EXCLU", "QUITA")):
                current["motivo_encerramento"] = line[:120]

        flush_current()
        return contracts

    def _fill_missing_contract_totals(
        self, text: str, contracts: list[LoanContractResult]
    ) -> None:
        def pick_labeled_currency(window: str, labels: tuple[str, ...]) -> tuple[float, str] | None:
            for raw_line in window.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                normalized = self._normalize_for_match(line)
                if not any(label in normalized for label in labels):
                    continue
                value = self._extract_brl_from_line(line)
                if value is None:
                    continue
                return (value, line)
            return None

        for contract in contracts:
            if contract.valor_total and contract.valor_total.value is not None:
                continue
            if not contract.contract_id:
                continue
            idx = text.find(contract.contract_id)
            if idx == -1:
                continue
            window = text[idx : idx + 800]

            explicit_total = pick_labeled_currency(
                window,
                (
                    "VALOR TOTAL",
                    "TOTAL DO CONTRATO",
                    "TOTAL A PAGAR",
                    "VALOR FINANCIADO",
                ),
            )
            if explicit_total:
                contract.valor_total = ExtractedField(
                    value=explicit_total[0],
                    currency="BRL",
                    method="EXTRACTED_FROM_STATEMENT_REGEX",
                    evidence=FieldEvidence(page=0, text=explicit_total[1]),
                )
                contract.alerts.append(
                    "Valor total preenchido por linha explicitamente rotulada."
                )
                continue

            labeled_emprestado = pick_labeled_currency(
                window,
                ("VALOR EMPRESTADO", "EMPRESTADO LIBERADO", "VALOR LIBERADO"),
            )
            currency_vals = self._parse_currency_values(window)
            if not currency_vals:
                continue
            chosen = None
            if len(currency_vals) >= 2:
                chosen = currency_vals[1]
            elif len(currency_vals) == 1 and contract.parcela_mensal.value is None:
                chosen = currency_vals[0]

            if chosen and labeled_emprestado:
                if abs(chosen[0] - labeled_emprestado[0]) < 0.01:
                    chosen = None

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
        by_parcela: dict[float, list[LoanContractResult]] = {}
        for c in primary:
            if c.parcela_mensal.value is None:
                continue
            lender_norm = self._normalize_for_match(c.lender_name or "")
            if lender_norm.startswith("CARTAO"):
                continue
            key = round(float(c.parcela_mensal.value), 2)
            by_parcela.setdefault(key, []).append(c)
        merged = list(primary)

        def merge_into(base: LoanContractResult, fb: LoanContractResult) -> None:
            original_id = base.contract_id
            if (not base.contract_id) and fb.contract_id:
                base.contract_id = fb.contract_id
            elif base.contract_id and fb.contract_id:
                if (
                    base.contract_id != fb.contract_id
                    and base.contract_id in fb.contract_id
                    and len(fb.contract_id) > len(base.contract_id)
                ):
                    base.contract_id = fb.contract_id
            if base.contract_id != original_id:
                if original_id:
                    by_id.pop(original_id, None)
                if base.contract_id:
                    by_id[base.contract_id] = base

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
            if base.taxa_juros is None and fb.taxa_juros is not None:
                base.taxa_juros = fb.taxa_juros
            if base.cet_mensal is None and fb.cet_mensal is not None:
                base.cet_mensal = fb.cet_mensal
            if base.cet_anual is None and fb.cet_anual is not None:
                base.cet_anual = fb.cet_anual
            if base.iof_cent is None and fb.iof_cent is not None:
                base.iof_cent = fb.iof_cent
            if (
                base.valor_emprestado_cent is None
                and fb.valor_emprestado_cent is not None
            ):
                base.valor_emprestado_cent = fb.valor_emprestado_cent
            if base.status is None and fb.status is not None:
                base.status = fb.status
            if fb.alerts:
                base.alerts.extend(fb.alerts)

        for fb in fallback:
            if fb.contract_id and fb.contract_id in by_id:
                merge_into(by_id[fb.contract_id], fb)
                continue

            if fb.parcela_mensal.value is not None:
                key = round(float(fb.parcela_mensal.value), 2)
                candidates = by_parcela.get(key, [])
                if candidates:
                    target = None
                    if len(candidates) == 1:
                        target = candidates[0]
                    elif fb.lender_name:
                        fb_lender = self._normalize_for_match(fb.lender_name)
                        for candidate in candidates:
                            candidate_lender = self._normalize_for_match(
                                candidate.lender_name or ""
                            )
                            if fb_lender and candidate_lender and (
                                fb_lender in candidate_lender
                                or candidate_lender in fb_lender
                            ):
                                target = candidate
                                break
                    if target:
                        merge_into(target, fb)
                        if target.valor_total.value is None and fb.valor_total.value is not None:
                            target.alerts.append(
                                "Valor total preenchido por fallback regex (match por parcela)."
                            )
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
        Retorna como pseudo-contratos para compor consignado mensal e dívida total.
        """
        results: list[LoanContractResult] = []

        def build_card_result(
            card_label: str,
            limit_value: float | None,
            limit_evidence: str | None,
            margin_value: float | None,
            margin_evidence: str | None,
        ) -> LoanContractResult:
            parcela_field = ExtractedField(None, None, None, None)
            if margin_value is not None:
                parcela_field = ExtractedField(
                    value=margin_value,
                    currency="BRL",
                    method="EXTRACTED_FROM_CARD_MARGIN",
                    evidence=FieldEvidence(page=0, text=margin_evidence or ""),
                )

            valor_total_field = ExtractedField(None, None, None, None)
            if limit_value is not None:
                valor_total_field = ExtractedField(
                    value=limit_value,
                    currency="BRL",
                    method="EXTRACTED_FROM_CARD_LIMIT",
                    evidence=FieldEvidence(page=0, text=limit_evidence or ""),
                )

            alerts = [
                "Limite de cartão consignado (RMC/RCC) incluído na dívida total."
            ]
            if margin_value is not None:
                alerts.append(
                    "Valor de cartão consignado (RMC/RCC) incluído no consignado mensal."
                )

            return LoanContractResult(
                lender_name=f"CARTAO {card_label}",
                contract_id=None,
                parcela_mensal=parcela_field,
                total_parcelas=None,
                parcelas_pagas=None,
                parcelas_restantes=None,
                valor_total=valor_total_field,
                taxa_juros=None,
                alerts=alerts,
                status="ATIVO",
            )

        lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]

        seen: set[tuple[str, float | None, float | None]] = set()

        def extract_by_marker(marker: str, card_label: str) -> None:
            marker_norm = self._normalize_for_match(marker)
            for idx in range(len(lines)):
                chunk = " ".join(lines[idx : idx + 4])
                if marker_norm not in self._normalize_for_match(chunk):
                    continue
                start = max(0, idx - 18)
                end = min(len(lines), idx + 6)
                window = "\n".join(lines[start:end])
                values = self._parse_currency_values(window)
                if not values:
                    continue
                # Escolher maior valor como limite e menor como margem
                values_sorted = sorted(values, key=lambda item: item[0])
                margin_value, margin_evidence = values_sorted[0]
                limit_value, limit_evidence = values_sorted[-1]
                key = (card_label, limit_value, margin_value)
                if key in seen:
                    continue
                seen.add(key)
                results.append(
                    build_card_result(
                        card_label,
                        limit_value,
                        limit_evidence,
                        margin_value,
                        margin_evidence,
                    )
                )

        extract_by_marker("Reserva de Margem para Cartão (RMC)", "RMC")
        extract_by_marker("Reserva de Cartão Consignado (RCC)", "RCC")

        if results:
            return results

        # 1) Preferir seção "Margem para Empréstimo/Cartão e Resumo Financeiro"
        header_match = re.search(
            r"Margem\s+para\s+Empr[ée]stimo/Cart[ãa]o\s+e\s+Resumo\s+Financeiro",
            text,
            flags=re.IGNORECASE,
        )
        if header_match:
            start_idx = header_match.start()
            end_idx = None
            end_match = re.search(
                r"VALORES\s+POR\s+MODALIDADE|EMPR[ÉE]STIMOS\s+BANC[ÁA]RIOS",
                text[start_idx:],
                flags=re.IGNORECASE,
            )
            if end_match:
                end_idx = start_idx + end_match.start()
            block = text[start_idx:end_idx] if end_idx else text[start_idx:]
            normalized = re.sub(r"\s+", " ", block)
            card_match = re.search(
                r"\bRCC\b\s*R\$\s*([\d\.]+,\d{2})",
                normalized,
                flags=re.IGNORECASE,
            )
            if not card_match:
                card_match = re.search(
                    r"\bRMC\b\s*R\$\s*([\d\.]+,\d{2})",
                    normalized,
                    flags=re.IGNORECASE,
                )
            if card_match:
                values = self._parse_currency_values(f"R$ {card_match.group(1)}")
                if values:
                    value, evidence = values[0]
                    results.append(
                        build_card_result(
                            "RMC/RCC",
                            None,
                            None,
                            value,
                            evidence,
                        )
                    )

        # 2) Fallback para seção "VALOR LIMITE DE CARTÃO RESERVADO ATUALIZADO"
        if not results:
            pattern = re.compile(
                r"VALOR\s+LIMITE\s+DE\s+CART[ÃA]O\s+RESERVADO\s+ATUALIZADO(.*?)(?:VALORES\s+POR\s+MODALIDADE|\Z)",
                flags=re.IGNORECASE | re.DOTALL,
            )
            for match in pattern.finditer(text):
                block = match.group(0)
                values = self._parse_currency_values(block)
                if not values:
                    continue
                value, evidence = max(values, key=lambda item: item[0])
                results.append(
                    build_card_result(
                        "RMC/RCC",
                        value,
                        evidence,
                        None,
                        None,
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
                lender_name = " ".join(bank_name_parts)
                lender_name = re.sub(r"^\d{3}\s*-\s*", "", lender_name).strip()
                lender_name = re.sub(r"\s+", " ", lender_name).strip()
                if lender_name:
                    current["lender_name"] = lender_name

            block_text = "\n".join(block_lines)

            def pick_labeled_currency(labels: tuple[str, ...]) -> tuple[float, str] | None:
                for raw_line in block_lines:
                    line = raw_line.strip()
                    if not line:
                        continue
                    normalized_line = self._normalize_for_match(line)
                    if not any(label in normalized_line for label in labels):
                        continue
                    value = self._extract_brl_from_line(line)
                    if value is None:
                        continue
                    return (value, line)
                return None

            currency_vals = self._parse_currency_values(block_text)
            parcela_val = pick_labeled_currency(("PARCELA",))
            if parcela_val is None:
                parcela_val = currency_vals[0] if len(currency_vals) > 0 else None

            total_val = pick_labeled_currency(
                ("VALOR TOTAL", "TOTAL DO CONTRATO", "TOTAL A PAGAR", "VALOR FINANCIADO")
            )
            if total_val is None and len(currency_vals) > 1:
                total_val = currency_vals[1]

            emprestado_val = pick_labeled_currency(
                ("VALOR EMPRESTADO", "EMPRESTADO LIBERADO", "VALOR LIBERADO")
            )
            percentual_matches = re.findall(r"\d{1,2},\d{1,2}%", block_text)
            cet_mensal = percentual_matches[0] if len(percentual_matches) > 0 else None
            cet_anual = percentual_matches[1] if len(percentual_matches) > 1 else None
            iof_match = re.search(r"IOF.*?R\$\s*([\d\.]+,\d{2})", block_text, re.IGNORECASE)
            emprestado_match = re.search(
                r"(?:VALOR\s+EMPRESTADO|VALOR\s+LIBERADO).*?R\$\s*([\d\.]+,\d{2})",
                block_text,
                re.IGNORECASE,
            )
            normalized_block = re.sub(r"\s+", " ", block_text or "")
            status_marker = re.search(r"ATIVO|SUSPENS|EXCLU|ENCERR", normalized_block, re.IGNORECASE)
            if status_marker:
                pre_status_block = normalized_block[: status_marker.start()]
                post_status_block = normalized_block[status_marker.end() :]
            else:
                pre_status_block = normalized_block
                post_status_block = ""
            pre_status_currency_vals = self._parse_currency_values_strict(pre_status_block)

            if current.get("total_parcelas") is None:
                qtde_match = re.search(
                    r"(?:\d{2}/\d{4}\s+){1,2}(\d{1,3})\s+R\$\s*[\d\.]+\s*,\s*\d{2}",
                    pre_status_block,
                )
                if qtde_match:
                    current["total_parcelas"] = int(qtde_match.group(1))

            if emprestado_val is None and len(pre_status_currency_vals) > 1:
                emprestado_val = pre_status_currency_vals[1]

            iof_cent = self._parse_brl_to_cent(iof_match.group(1)) if iof_match else None
            if iof_cent is None and len(pre_status_currency_vals) > 2:
                iof_cent = int(round(pre_status_currency_vals[2][0] * 100))

            post_status_no_currency = re.sub(
                r"R\$\s*[\d\.]+\s*,\s*\d{2}",
                " ",
                post_status_block,
                flags=re.IGNORECASE,
            )
            rate_candidates = re.findall(
                r"(?<![\d\.])(\d{1,2},\d{2})(?!\d)", post_status_no_currency
            )
            if cet_mensal is None and len(rate_candidates) > 0:
                cet_mensal = f"{rate_candidates[0]}%"
            if cet_anual is None and len(rate_candidates) > 1:
                cet_anual = f"{rate_candidates[1]}%"
            taxa_juros = None
            if len(rate_candidates) > 2:
                taxa_juros = f"{rate_candidates[2]}%"

            inss_tabular_signature = iof_cent is not None and len(rate_candidates) >= 3

            total_parcelas = current.get("total_parcelas")
            if (
                total_val is not None
                and emprestado_val is not None
                and abs(total_val[0] - emprestado_val[0]) < 0.01
                and parcela_val is not None
                and isinstance(total_parcelas, int)
                and total_parcelas > 0
                and not inss_tabular_signature
            ):
                total_val = None

            alerts = ["Extração fallback por regex (LLM inválido ou sem JSON)."]
            if fallback_alert:
                alerts.append(fallback_alert)
            parcelas_restantes = current.get("parcelas_restantes")
            if (
                parcelas_restantes is None
                and isinstance(total_parcelas, int)
                and total_parcelas > 0
            ):
                parcelas_restantes = total_parcelas
                alerts.append(
                    "Parcelas restantes inferidas pelo fallback usando QTDE PARCELAS."
                )
            if (
                total_val is None
                and parcela_val is not None
                and isinstance(total_parcelas, int)
                and total_parcelas > 0
            ):
                alerts.append(
                    "Valor total ausente/ambíguo; será inferido por parcela x total de parcelas."
                )

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
                    parcelas_restantes=parcelas_restantes,
                    valor_total=total_field,
                    taxa_juros=self._normalize_rate_value(
                        current.get("taxa_juros") or taxa_juros or cet_mensal
                    ),
                    alerts=alerts,
                    status=current.get("status") or "ATIVO",
                    cet_mensal=self._normalize_rate_value(cet_mensal),
                    cet_anual=self._normalize_rate_value(cet_anual),
                    iof_cent=iof_cent,
                    valor_emprestado_cent=(
                        int(round(emprestado_val[0] * 100))
                        if emprestado_val
                        else (
                        self._parse_brl_to_cent(emprestado_match.group(1))
                        if emprestado_match
                        else None
                        )
                    ),
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

            if (
                current
                and current.get("status")
                and re.fullmatch(r"\d{5,}", line_clean)
            ):
                finalize_contract()

            bank_line = re.search(r"\b\d{3}\s*-\s*.+", line_clean)
            bank_line_prefix = re.search(r"\b\d{3}\s*-\s*$", line_clean)
            if bank_line or bank_line_prefix:
                if current:
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

            if (
                ("ATIVO" in line_upper or "SUSPENS" in line_upper)
                and (current or digit_buffer or bank_name_parts)
            ):
                current["status"] = "SUSPENSO" if "SUSPENS" in line_upper else "ATIVO"
                block_lines.append(line_clean)
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

            def parse_cent_field(raw_value) -> int | None:
                if raw_value is None:
                    return None
                if isinstance(raw_value, dict):
                    if raw_value.get("value") is not None:
                        try:
                            return int(round(float(raw_value.get("value")) * 100))
                        except (TypeError, ValueError):
                            return None
                    raw_value = raw_value.get("cent")
                if isinstance(raw_value, (int, float)):
                    return int(round(float(raw_value)))
                if isinstance(raw_value, str):
                    return self._parse_brl_to_cent(raw_value)
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

                total_parcelas = parse_int_field(item.get("totalParcelas"))
                parcelas_pagas = parse_int_field(item.get("parcelasPagas"))
                parcelas_restantes = parse_int_field(item.get("parcelasRestantes"))
                if (
                    parcelas_restantes is None
                    and total_parcelas is not None
                    and parcelas_pagas is None
                ):
                    parcelas_restantes = total_parcelas

                results.append(
                    LoanContractResult(
                        lender_name=item.get("lenderName"),
                        contract_id=item.get("contractId"),
                        parcela_mensal=parse_field(item.get("parcelaMensal")),
                        total_parcelas=total_parcelas,
                        parcelas_pagas=parcelas_pagas,
                        parcelas_restantes=parcelas_restantes,
                        valor_total=parse_field(item.get("valorTotal")),
                        taxa_juros=self._normalize_rate_value(item.get("taxaJuros")),
                        alerts=item_alerts,
                        status=item.get("status"),
                        cet_mensal=self._normalize_rate_value(item.get("cetMensal")),
                        cet_anual=self._normalize_rate_value(item.get("cetAnual")),
                        iof_cent=parse_cent_field(item.get("iof")),
                        valor_emprestado_cent=parse_cent_field(
                            item.get("valorEmprestado")
                        ),
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
                        status=None,
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
                    status=None,
                )
            ]
