"""
Compute Engine
~~~~~~~~~~~~~~

Executa cálculos determinísticos em centavos (BIGINT).
Baseado no PRD seção RF-010.
"""

from dataclasses import dataclass

from app.services.consolidator import ConsolidatedAlert, ConsolidatedData, ConsolidatedValue, DocumentSource


class ComputeMethod(str):
    """Métodos de cálculo."""

    DIFFERENCE = "DIFFERENCE"  # bruto - liquido
    SUM_LINES = "SUM_LINES"  # Soma de linhas
    SUM_CONTRACTS = "SUM_CONTRACTS"  # Soma de contratos
    EXTRACTED = "EXTRACTED"  # Extraído diretamente
    USER_DECLARED = "USER_DECLARED"  # Declarado pelo usuário
    NOT_APPLICABLE = "NOT_APPLICABLE"  # Não aplicável para o documento


@dataclass
class ComputeResult:
    """Resultado dos cálculos do Compute Engine."""

    # Valores calculados (em centavos)
    salario_bruto_cent: int | None
    salario_liquido_cent: int | None
    total_descontos_cent: int | None
    consignado_mensal_cent: int | None
    divida_total_consignada_cent: int | None
    parcelas_restantes_total: int | None

    # Metadata de cálculo
    descontos_method: str | None
    consignado_method: str | None
    divida_method: str | None
    parcelas_method: str | None

    # Provenance (fontes)
    bruto_source: str | None
    liquido_source: str | None

    # Alertas de cálculo
    alerts: list[ConsolidatedAlert]

    def to_dict_for_db(self) -> dict:
        """
        Converte resultado para dict compatível com banco de dados.

        Returns:
            Dicionário com todos os campos para persistência
        """
        return {
            "salario_bruto_cent": self.salario_bruto_cent,
            "salario_liquido_cent": self.salario_liquido_cent,
            "total_descontos_cent": self.total_descontos_cent,
            "consignado_mensal_cent": self.consignado_mensal_cent,
            "divida_total_consignada_cent": self.divida_total_consignada_cent,
            "parcelas_restantes_total": self.parcelas_restantes_total,
            "descontos_method": self.descontos_method,
            "consignado_method": self.consignado_method,
            "divida_method": self.divida_method,
            "parcelas_method": self.parcelas_method,
            "bruto_source": self.bruto_source,
            "liquido_source": self.liquido_source,
        }


class ComputeEngine:
    """
    Engine de cálculos determinísticos.

    Todos os cálculos são executados em centavos (BIGINT) para garantir
    precisão absoluta sem erros de arredondamento (RF-010 RN-001).
    """

    def compute(self, consolidated: ConsolidatedData) -> ComputeResult:
        """
        Executa todos os cálculos determinísticos.

        Args:
            consolidated: Dados consolidados do Consolidator

        Returns:
            Resultado com todos os valores calculados em centavos

        Baseado em RF-010.
        """
        alerts = list(consolidated.alerts)  # Copiar alertas existentes

        # Extrair valores consolidados
        bruto_cent = (
            consolidated.salario_bruto.value_cent
            if consolidated.salario_bruto
            else None
        )
        liquido_cent = (
            consolidated.salario_liquido.value_cent
            if consolidated.salario_liquido
            else None
        )
        descontos_cent = (
            consolidated.total_descontos.value_cent
            if consolidated.total_descontos
            else None
        )

        # Metadata de fonte
        bruto_source = (
            consolidated.salario_bruto.source.value
            if consolidated.salario_bruto
            else None
        )
        liquido_source = (
            consolidated.salario_liquido.source.value
            if consolidated.salario_liquido
            else None
        )

        # 1. Calcular total_descontos_cent (RF-010 CA-002)
        descontos_method = None
        if descontos_cent is None and bruto_cent is not None and liquido_cent is not None:
            # Calcular por diferença
            descontos_cent = bruto_cent - liquido_cent
            descontos_method = ComputeMethod.DIFFERENCE

            # Validar invariante: descontos não pode ser negativo
            if descontos_cent < 0:
                alerts.append(
                    ConsolidatedAlert(
                        field_name="total_descontos",
                        severity="ERROR",
                        message=f"Descontos calculado é negativo: {descontos_cent/100:.2f} (bruto < líquido)",
                    )
                )
                descontos_cent = None
                descontos_method = None
        elif descontos_cent is not None:
            descontos_method = ComputeMethod.EXTRACTED

        # 2. Calcular consignado_mensal_cent (RF-010 CA-003)
        consignado_cent = None
        consignado_method = None

        if consolidated.linhas_consignado:
            # Soma de linhas (método preferencial)
            consignado_cent = sum(
                linha.valor_cent for linha in consolidated.linhas_consignado
            )
            consignado_method = ComputeMethod.SUM_LINES
        elif consolidated.contratos:
            # Fallback: soma das parcelas mensais dos contratos
            contratos_com_parcela = [
                c for c in consolidated.contratos if c.parcela_mensal.value is not None
            ]
            if contratos_com_parcela:
                consignado_cent = sum(
                    int(c.parcela_mensal.value * 100) for c in contratos_com_parcela
                )
                consignado_method = ComputeMethod.SUM_CONTRACTS
        elif liquido_source == DocumentSource.INSS_HISTORICO_CREDITOS:
            # Histórico de créditos não consolida consignações
            consignado_cent = 0
            consignado_method = ComputeMethod.NOT_APPLICABLE

        # 3. Calcular dívida total consignada (RF-010 CA-004)
        divida_cent = None
        divida_method = None

        if consolidated.contratos:
            # Soma de contratos ativos
            contratos_com_valor = [
                c for c in consolidated.contratos if c.valor_total.value is not None
            ]

            if contratos_com_valor:
                divida_cent = sum(
                    int(c.valor_total.value * 100) for c in contratos_com_valor
                )
                divida_method = ComputeMethod.SUM_CONTRACTS

        # 4. Calcular parcelas restantes total (RF-010 CA-005)
        parcelas_restantes = None
        parcelas_method = None

        if consolidated.contratos:
            # Soma de parcelas restantes de todos os contratos
            parcelas_list = []

            for contrato in consolidated.contratos:
                if contrato.parcelas_restantes is not None:
                    parcelas_list.append(contrato.parcelas_restantes)
                elif (
                    contrato.total_parcelas is not None
                    and contrato.parcelas_pagas is not None
                ):
                    # Calcular: restantes = total - pagas
                    restantes = contrato.total_parcelas - contrato.parcelas_pagas
                    parcelas_list.append(restantes)

            if parcelas_list:
                parcelas_restantes = sum(parcelas_list)
                parcelas_method = ComputeMethod.SUM_CONTRACTS

        # 5. Validar invariantes matemáticos (RF-010 CA-006 implícito)
        if bruto_cent is not None and liquido_cent is not None:
            if bruto_cent < liquido_cent:
                alerts.append(
                    ConsolidatedAlert(
                        field_name="invariant_bruto_liquido",
                        severity="ERROR",
                        message=f"Salário bruto ({bruto_cent/100:.2f}) não pode ser menor que líquido ({liquido_cent/100:.2f})",
                    )
                )

        if descontos_cent is not None and descontos_cent < 0:
            alerts.append(
                ConsolidatedAlert(
                    field_name="invariant_descontos",
                    severity="ERROR",
                    message=f"Total de descontos não pode ser negativo: {descontos_cent/100:.2f}",
                )
            )

        if consignado_cent is not None and consignado_cent < 0:
            alerts.append(
                ConsolidatedAlert(
                    field_name="invariant_consignado",
                    severity="ERROR",
                    message=f"Consignado mensal não pode ser negativo: {consignado_cent/100:.2f}",
                )
            )

        if divida_cent is not None and divida_cent < 0:
            alerts.append(
                ConsolidatedAlert(
                    field_name="invariant_divida",
                    severity="ERROR",
                    message=f"Dívida total não pode ser negativa: {divida_cent/100:.2f}",
                )
            )

        return ComputeResult(
            salario_bruto_cent=bruto_cent,
            salario_liquido_cent=liquido_cent,
            total_descontos_cent=descontos_cent,
            consignado_mensal_cent=consignado_cent,
            divida_total_consignada_cent=divida_cent,
            parcelas_restantes_total=parcelas_restantes,
            descontos_method=descontos_method,
            consignado_method=consignado_method,
            divida_method=divida_method,
            parcelas_method=parcelas_method,
            bruto_source=bruto_source,
            liquido_source=liquido_source,
            alerts=alerts,
        )

    @staticmethod
    def cents_to_currency(cents: int | None) -> float | None:
        """
        Converte centavos para valor monetário (RF-010 CA-006).

        Args:
            cents: Valor em centavos

        Returns:
            Valor em moeda com 2 casas decimais
        """
        if cents is None:
            return None
        return cents / 100.0

    @staticmethod
    def currency_to_cents(value: float | None) -> int | None:
        """
        Converte valor monetário para centavos.

        Args:
            value: Valor em moeda

        Returns:
            Valor em centavos (BIGINT)
        """
        if value is None:
            return None
        return int(value * 100)
