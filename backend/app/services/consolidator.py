"""
Consolidator Service
~~~~~~~~~~~~~~~~~~~~

Consolida dados de múltiplas fontes e seleciona competência alvo.
Baseado no PRD seções RF-008 e RF-009.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.services.extractors import (
    ConsignadoLine,
    LoanContractResult,
    PaymentExtractionResult,
)


class DocumentSource(str, Enum):
    """Fonte do documento."""

    PAYROLL_SALARY_STATEMENT = "PAYROLL_SALARY_STATEMENT"
    INSS_HISTORICO_CREDITOS = "INSS_HISTORICO_CREDITOS"
    INSS_EXTRATO_CONSIGNADO = "INSS_EXTRATO_CONSIGNADO"
    LOAN_CONTRACT = "LOAN_CONTRACT"
    DECLARADO = "DECLARADO"  # Valor declarado pelo usuário


class SourcePriority(int, Enum):
    """Prioridade de fonte (menor = mais prioritário)."""

    HIGHEST = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class ConsolidatedValue:
    """Valor consolidado com metadata de provenance."""

    value_cent: int | None  # Valor em centavos
    source: DocumentSource  # Fonte do valor
    method: str  # Método de extração/cálculo
    document_id: str | None  # ID do documento de origem
    confidence: float  # Confiança (0-1)


@dataclass
class ConsolidatedAlert:
    """Alerta de consolidação."""

    field_name: str
    severity: str  # "WARN" ou "ERROR"
    message: str
    conflicting_values: list[ConsolidatedValue] | None = None


@dataclass
class ConsolidatedData:
    """Dados consolidados de todos os documentos."""

    competencia_alvo: str  # Formato YYYY-MM
    salario_bruto: ConsolidatedValue | None
    salario_liquido: ConsolidatedValue | None
    total_descontos: ConsolidatedValue | None
    consignado_mensal: ConsolidatedValue | None
    divida_total_consignada: ConsolidatedValue | None
    parcelas_restantes_total: int | None
    linhas_consignado: list[ConsignadoLine]  # Todas as linhas consolidadas
    contratos: list[LoanContractResult]  # Todos os contratos
    alerts: list[ConsolidatedAlert]


class ConsolidatorService:
    """Serviço de consolidação de múltiplas fontes."""

    # Regras de prioridade por campo (RF-009 RN-001, RN-002, RN-003)
    PRIORITY_RULES = {
        "salario_bruto": {
            DocumentSource.PAYROLL_SALARY_STATEMENT: SourcePriority.HIGHEST,
            DocumentSource.INSS_HISTORICO_CREDITOS: SourcePriority.HIGH,
        },
        "salario_liquido": {
            DocumentSource.INSS_HISTORICO_CREDITOS: SourcePriority.HIGHEST,
            DocumentSource.PAYROLL_SALARY_STATEMENT: SourcePriority.HIGH,
            DocumentSource.DECLARADO: SourcePriority.LOW,
        },
        "total_descontos": {
            DocumentSource.PAYROLL_SALARY_STATEMENT: SourcePriority.HIGHEST,
        },
        "consignado_mensal": {
            DocumentSource.PAYROLL_SALARY_STATEMENT: SourcePriority.HIGHEST,
            DocumentSource.INSS_EXTRATO_CONSIGNADO: SourcePriority.HIGH,
            DocumentSource.LOAN_CONTRACT: SourcePriority.MEDIUM,  # Estimado
        },
    }

    def __init__(self, conflict_tolerance_percent: float = 1.0):
        """
        Inicializa Consolidator.

        Args:
            conflict_tolerance_percent: Tolerância para conflitos (padrão 1%)
        """
        self.conflict_tolerance = conflict_tolerance_percent / 100.0

    def _normalize_competencia(self, competencia: str) -> str | None:
        """
        Normaliza competência para formato YYYY-MM.

        Args:
            competencia: Competência em diversos formatos (MM/YYYY, YYYY-MM, etc)

        Returns:
            Competência normalizada ou None se inválida

        Examples:
            >>> _normalize_competencia("01/2026")
            "2026-01"
            >>> _normalize_competencia("2026-01")
            "2026-01"
            >>> _normalize_competencia("012026")
            "2026-01"
        """
        if not competencia:
            return None

        # Padrão MM/YYYY
        match = re.match(r"(\d{2})/(\d{4})", competencia)
        if match:
            mm, yyyy = match.groups()
            return f"{yyyy}-{mm}"

        # Padrão YYYY-MM
        match = re.match(r"(\d{4})-(\d{2})", competencia)
        if match:
            return competencia

        # Padrão MMYYYY (6 dígitos)
        match = re.match(r"(\d{2})(\d{4})", competencia)
        if match:
            mm, yyyy = match.groups()
            return f"{yyyy}-{mm}"

        return None

    def select_target_competencia(
        self, payment_results: list[PaymentExtractionResult]
    ) -> tuple[str, ConsolidatedAlert | None]:
        """
        Seleciona competência alvo (a mais recente).

        Args:
            payment_results: Resultados de extração de folhas

        Returns:
            Tupla (competencia_alvo, alerta opcional)

        Baseado em RF-008.
        """
        competencias = []

        # Coletar todas as competências (RF-008 CA-001)
        for result in payment_results:
            if result.competencia:
                normalized = self._normalize_competencia(result.competencia)
                if normalized:
                    competencias.append(normalized)

        # Remover duplicatas e ordenar (RF-008 CA-003)
        competencias = sorted(set(competencias), reverse=True)

        # Selecionar mais recente (RF-008 CA-003)
        if competencias:
            return competencias[0], None

        # Nenhuma competência encontrada - usar atual (RF-008 FE-001)
        now = datetime.now()
        current_competencia = now.strftime("%Y-%m")

        alert = ConsolidatedAlert(
            field_name="competencia_alvo",
            severity="WARN",
            message=f"Nenhuma competência detectada. Usando {current_competencia} (atual).",
        )

        return current_competencia, alert

    def _get_priority(
        self, field_name: str, source: DocumentSource
    ) -> SourcePriority:
        """
        Obtém prioridade de uma fonte para um campo.

        Args:
            field_name: Nome do campo
            source: Fonte do valor

        Returns:
            Prioridade (menor = mais prioritário)
        """
        rules = self.PRIORITY_RULES.get(field_name, {})
        return rules.get(source, SourcePriority.LOW)

    def _consolidate_field(
        self,
        field_name: str,
        candidates: list[ConsolidatedValue],
    ) -> tuple[ConsolidatedValue | None, list[ConsolidatedAlert]]:
        """
        Consolida um campo específico selecionando melhor candidato.

        Args:
            field_name: Nome do campo
            candidates: Lista de candidatos

        Returns:
            Tupla (valor consolidado, alertas)

        Baseado em RF-009 CA-001, CA-002, CA-003.
        """
        if not candidates:
            return None, []

        # Filtrar candidatos válidos (com valor)
        valid_candidates = [c for c in candidates if c.value_cent is not None]
        if not valid_candidates:
            return None, []

        # Ordenar por prioridade (RF-009 CA-002)
        valid_candidates.sort(
            key=lambda c: (
                self._get_priority(field_name, c.source),
                -c.confidence,  # Desempate por confiança
            )
        )

        # Selecionar melhor candidato
        best = valid_candidates[0]

        # Verificar conflitos com mesma prioridade (RF-009 CA-003)
        alerts = []
        best_priority = self._get_priority(field_name, best.source)
        same_priority = [
            c
            for c in valid_candidates
            if self._get_priority(field_name, c.source) == best_priority
        ]

        if len(same_priority) > 1:
            # Checar divergência
            values = [c.value_cent for c in same_priority if c.value_cent]
            if values:
                min_val = min(values)
                max_val = max(values)
                if min_val > 0:  # Evitar divisão por zero
                    divergence = (max_val - min_val) / min_val
                    if divergence > self.conflict_tolerance:
                        alerts.append(
                            ConsolidatedAlert(
                                field_name=field_name,
                                severity="WARN",
                                message=f"Conflito detectado: divergência de {divergence*100:.1f}% entre fontes de mesma prioridade",
                                conflicting_values=same_priority,
                            )
                        )

        return best, alerts

    def consolidate(
        self,
        payment_results: list[PaymentExtractionResult],
        loan_results: list[LoanContractResult],
        doc_sources: dict[str, DocumentSource],  # Mapeia document_id -> fonte
        renda_mensal_declarada_cent: int | None = None,
    ) -> ConsolidatedData:
        """
        Consolida todos os dados de múltiplas fontes.

        Args:
            payment_results: Resultados de extração de folhas
            loan_results: Resultados de extração de contratos
            doc_sources: Mapa de document_id para tipo de fonte
            renda_mensal_declarada_cent: Renda declarada pelo usuário (fallback)

        Returns:
            Dados consolidados com alertas

        Baseado em RF-008 e RF-009.
        """
        alerts = []

        # 1. Selecionar competência alvo (RF-008)
        competencia_alvo, comp_alert = self.select_target_competencia(
            payment_results
        )
        if comp_alert:
            alerts.append(comp_alert)

        # 2. Coletar candidatos para cada campo (RF-009 CA-001)
        bruto_candidates = []
        liquido_candidates = []
        descontos_candidates = []
        linhas_consignado_all = []

        for i, result in enumerate(payment_results):
            # Filtrar apenas resultados da competência alvo
            result_comp = self._normalize_competencia(result.competencia or "")
            if result_comp != competencia_alvo:
                continue

            doc_id = f"payment_{i}"
            source = doc_sources.get(doc_id, DocumentSource.PAYROLL_SALARY_STATEMENT)

            # Salário bruto
            if result.salario_bruto.value is not None:
                bruto_candidates.append(
                    ConsolidatedValue(
                        value_cent=int(result.salario_bruto.value * 100),
                        source=source,
                        method=result.salario_bruto.method or "EXTRACTED",
                        document_id=doc_id,
                        confidence=1.0,
                    )
                )

            # Salário líquido
            if result.salario_liquido.value is not None:
                liquido_candidates.append(
                    ConsolidatedValue(
                        value_cent=int(result.salario_liquido.value * 100),
                        source=source,
                        method=result.salario_liquido.method or "EXTRACTED",
                        document_id=doc_id,
                        confidence=1.0,
                    )
                )

            # Total descontos
            if result.total_descontos.value is not None:
                descontos_candidates.append(
                    ConsolidatedValue(
                        value_cent=int(result.total_descontos.value * 100),
                        source=source,
                        method=result.total_descontos.method or "EXTRACTED",
                        document_id=doc_id,
                        confidence=1.0,
                    )
                )

            # Linhas de consignado
            linhas_consignado_all.extend(result.linhas_consignado)

        # Fallback: renda declarada (RF-009 FA-001)
        if not liquido_candidates and renda_mensal_declarada_cent:
            liquido_candidates.append(
                ConsolidatedValue(
                    value_cent=renda_mensal_declarada_cent,
                    source=DocumentSource.DECLARADO,
                    method="USER_DECLARED",
                    document_id=None,
                    confidence=0.5,
                )
            )

        # 3. Consolidar cada campo (RF-009 CA-002)
        salario_bruto, bruto_alerts = self._consolidate_field(
            "salario_bruto", bruto_candidates
        )
        alerts.extend(bruto_alerts)

        salario_liquido, liquido_alerts = self._consolidate_field(
            "salario_liquido", liquido_candidates
        )
        alerts.extend(liquido_alerts)

        total_descontos, descontos_alerts = self._consolidate_field(
            "total_descontos", descontos_candidates
        )
        alerts.extend(descontos_alerts)

        return ConsolidatedData(
            competencia_alvo=competencia_alvo,
            salario_bruto=salario_bruto,
            salario_liquido=salario_liquido,
            total_descontos=total_descontos,
            consignado_mensal=None,  # Será calculado pelo Compute Engine
            divida_total_consignada=None,  # Será calculado pelo Compute Engine
            parcelas_restantes_total=None,  # Será calculado pelo Compute Engine
            linhas_consignado=linhas_consignado_all,
            contratos=loan_results,
            alerts=alerts,
        )
