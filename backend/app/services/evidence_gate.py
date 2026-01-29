"""
Evidence Gate Service
~~~~~~~~~~~~~~~~~~~~~

Validação determinística de valores extraídos por LLM.
Garante que o LLM não "alucinou" valores através de re-parsing das evidências.

Baseado no PRD seção RF-007.
"""

import re
from dataclasses import dataclass
from enum import Enum

from app.services.extractors import (
    ExtractedField,
    LoanContractResult,
    PaymentExtractionResult,
)


class GateStatus(str, Enum):
    """Status da validação do Evidence Gate."""

    PASSED = "PASSED"  # Todos os campos validados OK
    WARN = "WARN"  # Alguns campos falharam (não críticos)
    FAILED = "FAILED"  # Campos críticos falharam


@dataclass
class ValidationAlert:
    """Alerta de validação."""

    field_name: str
    extracted_value: float | None
    reparsed_value: float | None
    evidence_text: str
    reason: str
    is_critical: bool


@dataclass
class GateResult:
    """Resultado da validação do Evidence Gate."""

    gate_status: GateStatus
    alerts: list[ValidationAlert]
    validated_fields: int
    failed_fields: int


class BrazilianCurrencyParser:
    """
    Parser de valores monetários brasileiros.

    Aceita formatos:
    - "R$ 1.334,36"
    - "1.334,36"
    - "1334,36"
    - "1.334"
    - "1334"
    """

    # Regex para capturar valores BR (RN-001)
    # Padrão: Opcional R$ + dígitos com pontos/vírgulas
    # Aceita: "R$ 1.334,36", "1.334,36", "1334,36", "1.334", "1334"
    # Ordem das alternativas é importante:
    # 1. Números com decimais (prioridade para capturar ,XX)
    # 2. Formato brasileiro com separadores de milhares
    # 3. Números inteiros simples
    CURRENCY_PATTERN = re.compile(
        r"(?:R\$\s*)?"  # R$ opcional com espaço opcional
        r"(\d+,\d{2}|\d{1,3}(?:\.\d{3})+(?:,\d{2})?|\d+)"  # Valor: decimal OU BR-format OU inteiro
    )

    @classmethod
    def parse(cls, text: str) -> float | None:
        """
        Extrai e normaliza valor monetário de texto.

        Args:
            text: Texto contendo valor (ex: "R$ 1.334,36")

        Returns:
            Valor normalizado em float ou None se não encontrado

        Examples:
            >>> parse("R$ 1.334,36")
            1334.36
            >>> parse("Total: 1.334,36")
            1334.36
            >>> parse("1334,36")
            1334.36
        """
        if not text:
            return None

        # Procurar padrão de moeda
        match = cls.CURRENCY_PATTERN.search(text)
        if not match:
            return None

        value_str = match.group(1)

        # Normalizar para formato americano
        # Remove pontos (separador de milhares)
        value_str = value_str.replace(".", "")
        # Substitui vírgula por ponto (separador decimal)
        value_str = value_str.replace(",", ".")

        try:
            return float(value_str)
        except ValueError:
            return None

    @classmethod
    def parse_all(cls, text: str) -> list[float]:
        """
        Extrai todos os valores monetários do texto.

        Args:
            text: Texto contendo múltiplos valores

        Returns:
            Lista de valores encontrados
        """
        values = []
        for match in cls.CURRENCY_PATTERN.finditer(text):
            value_str = match.group(1)
            value_str = value_str.replace(".", "").replace(",", ".")
            try:
                values.append(float(value_str))
            except ValueError:
                continue
        return values


class EvidenceGate:
    """
    Evidence Gate - Validação determinística de valores extraídos.

    Valida que valores extraídos pelo LLM correspondem às evidências.
    """

    def __init__(self, tolerance: float = 0.01):
        """
        Inicializa Evidence Gate.

        Args:
            tolerance: Tolerância para comparação de valores (padrão ±0.01)
        """
        self.tolerance = tolerance
        self.parser = BrazilianCurrencyParser()

    def _validate_field(
        self,
        field_name: str,
        field: ExtractedField,
        is_critical: bool = False,
    ) -> ValidationAlert | None:
        """
        Valida um campo individual.

        Args:
            field_name: Nome do campo
            field: Campo extraído com evidência
            is_critical: Se é campo crítico (reprova gate)

        Returns:
            ValidationAlert se validação falhou, None se passou
        """
        # Se campo é None, não validar
        if field.value is None:
            return None

        # Se não tem evidência, rejeitar
        if not field.evidence or not field.evidence.text:
            return ValidationAlert(
                field_name=field_name,
                extracted_value=float(field.value) if field.value else None,
                reparsed_value=None,
                evidence_text="",
                reason="Evidência ausente",
                is_critical=is_critical,
            )

        # Re-parsear evidência
        reparsed_value = self.parser.parse(field.evidence.text)

        # Se não conseguiu parsear, rejeitar (FE-001)
        if reparsed_value is None:
            return ValidationAlert(
                field_name=field_name,
                extracted_value=float(field.value) if field.value else None,
                reparsed_value=None,
                evidence_text=field.evidence.text,
                reason="Evidência não contém valor parseável",
                is_critical=is_critical,
            )

        # Comparar valores (CA-003)
        extracted_float = float(field.value)
        diff = abs(extracted_float - reparsed_value)

        if diff > self.tolerance:
            return ValidationAlert(
                field_name=field_name,
                extracted_value=extracted_float,
                reparsed_value=reparsed_value,
                evidence_text=field.evidence.text,
                reason=f"Divergência de {diff:.2f} (tolerância: {self.tolerance})",
                is_critical=is_critical,
            )

        # Validação passou
        return None

    def validate_payment_extraction(
        self, result: PaymentExtractionResult
    ) -> GateResult:
        """
        Valida extração de folha de pagamento.

        Args:
            result: Resultado da extração do Payment Extractor

        Returns:
            GateResult com status e alertas
        """
        alerts: list[ValidationAlert] = []
        validated_count = 0
        failed_count = 0

        # Validar campos críticos (RN-002)
        critical_fields = [
            ("salarioBruto", result.salario_bruto, True),
            ("salarioLiquido", result.salario_liquido, True),
        ]

        # Validar campos opcionais (RN-003)
        optional_fields = [
            ("totalDescontos", result.total_descontos, False),
        ]

        # Validar todos os campos
        for field_name, field, is_critical in critical_fields + optional_fields:
            if field.value is not None:
                validated_count += 1
                alert = self._validate_field(field_name, field, is_critical)
                if alert:
                    failed_count += 1
                    alerts.append(alert)

        # Validar linhas de consignado
        for i, linha in enumerate(result.linhas_consignado):
            validated_count += 1
            valor_brl = linha.valor_cent / 100
            reparsed = self.parser.parse(linha.evidence.text)

            if reparsed is None:
                failed_count += 1
                alerts.append(
                    ValidationAlert(
                        field_name=f"linhaConsignado[{i}]",
                        extracted_value=valor_brl,
                        reparsed_value=None,
                        evidence_text=linha.evidence.text,
                        reason="Evidência não contém valor parseável",
                        is_critical=False,
                    )
                )
            elif abs(valor_brl - reparsed) > self.tolerance:
                failed_count += 1
                alerts.append(
                    ValidationAlert(
                        field_name=f"linhaConsignado[{i}]",
                        extracted_value=valor_brl,
                        reparsed_value=reparsed,
                        evidence_text=linha.evidence.text,
                        reason=f"Divergência de {abs(valor_brl - reparsed):.2f}",
                        is_critical=False,
                    )
                )

        # Validar invariantes matemáticos (CA-005)
        if result.salario_bruto.value and result.salario_liquido.value:
            bruto = float(result.salario_bruto.value)
            liquido = float(result.salario_liquido.value)

            if bruto < liquido:
                alerts.append(
                    ValidationAlert(
                        field_name="invariant_bruto_liquido",
                        extracted_value=bruto,
                        reparsed_value=liquido,
                        evidence_text="",
                        reason="Salário bruto não pode ser menor que líquido",
                        is_critical=True,
                    )
                )
                failed_count += 1

        if result.total_descontos.value:
            descontos = float(result.total_descontos.value)
            if descontos < 0:
                alerts.append(
                    ValidationAlert(
                        field_name="invariant_descontos",
                        extracted_value=descontos,
                        reparsed_value=None,
                        evidence_text="",
                        reason="Total de descontos não pode ser negativo",
                        is_critical=False,
                    )
                )
                failed_count += 1

        # Determinar gate_status (CA-006)
        critical_failed = any(alert.is_critical for alert in alerts)

        if critical_failed:
            gate_status = GateStatus.FAILED
        elif failed_count > 0:
            gate_status = GateStatus.WARN
        else:
            gate_status = GateStatus.PASSED

        return GateResult(
            gate_status=gate_status,
            alerts=alerts,
            validated_fields=validated_count,
            failed_fields=failed_count,
        )

    def validate_loan_extraction(self, result: LoanContractResult) -> GateResult:
        """
        Valida extração de contrato de empréstimo.

        Args:
            result: Resultado da extração do Loan Extractor

        Returns:
            GateResult com status e alertas
        """
        alerts: list[ValidationAlert] = []
        validated_count = 0
        failed_count = 0

        # Validar campos críticos
        critical_fields = [
            ("parcelaMensal", result.parcela_mensal, True),
        ]

        # Validar campos opcionais
        optional_fields = [
            ("valorTotal", result.valor_total, False),
        ]

        # Validar todos os campos
        for field_name, field, is_critical in critical_fields + optional_fields:
            if field.value is not None:
                validated_count += 1
                alert = self._validate_field(field_name, field, is_critical)
                if alert:
                    failed_count += 1
                    alerts.append(alert)

        # Validar invariantes
        if result.parcela_mensal.value:
            parcela = float(result.parcela_mensal.value)
            if parcela < 0:
                alerts.append(
                    ValidationAlert(
                        field_name="invariant_parcela",
                        extracted_value=parcela,
                        reparsed_value=None,
                        evidence_text="",
                        reason="Parcela mensal não pode ser negativa",
                        is_critical=True,
                    )
                )
                failed_count += 1

        if result.total_parcelas is not None and result.total_parcelas < 0:
            alerts.append(
                ValidationAlert(
                    field_name="invariant_total_parcelas",
                    extracted_value=float(result.total_parcelas),
                    reparsed_value=None,
                    evidence_text="",
                    reason="Total de parcelas não pode ser negativo",
                    is_critical=False,
                )
            )
            failed_count += 1

        # Determinar gate_status
        critical_failed = any(alert.is_critical for alert in alerts)

        if critical_failed:
            gate_status = GateStatus.FAILED
        elif failed_count > 0:
            gate_status = GateStatus.WARN
        else:
            gate_status = GateStatus.PASSED

        return GateResult(
            gate_status=gate_status,
            alerts=alerts,
            validated_fields=validated_count,
            failed_fields=failed_count,
        )
