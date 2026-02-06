"""
Savings Simulator - Simulação de economia por portabilidade.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, getcontext
import re
from typing import Any

getcontext().prec = 28


@dataclass
class SavingsContractSimulation:
    contract_key: str
    lender_name: str
    parcela_atual_cent: int
    parcela_nova_estimada_cent: int
    economia_mensal_cent: int
    economia_total_restante_cent: int
    parcelas_restantes: int
    taxa_atual_mensal_percent: str
    taxa_referencia_mensal_percent: str


@dataclass
class SavingsSimulationResult:
    contratos: list[SavingsContractSimulation]
    economia_mensal_total_cent: int
    economia_total_restante_cent: int
    taxa_referencia_mensal_percent: str
    disclaimer: str


class SavingsSimulator:
    """Simula portabilidade usando aproximação Price em centavos."""

    def _parse_percent_to_decimal(self, value: str | None) -> Decimal | None:
        if not value:
            return None
        match = re.search(r"(\d{1,2}(?:[.,]\d{1,4})?)", value)
        if not match:
            return None
        normalized = match.group(1).replace(",", ".")
        try:
            return Decimal(normalized) / Decimal("100")
        except Exception:
            return None

    def _to_decimal_cent(self, value_cent: int) -> Decimal:
        return Decimal(value_cent) / Decimal("100")

    def _to_cent(self, value: Decimal) -> int:
        return int((value * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    def simulate_refinancing(
        self,
        contracts: list[Any],
        taxa_referencia_mensal: float = 1.50,
    ) -> SavingsSimulationResult:
        """
        Simula economia por contrato.
        Exclui contratos sem taxa atual, parcela ou parcelas restantes.
        """
        taxa_ref_decimal = Decimal(str(taxa_referencia_mensal)) / Decimal("100")
        taxa_ref_percent = f"{str(taxa_referencia_mensal).replace('.', ',')}%"

        simulations: list[SavingsContractSimulation] = []

        for contract in contracts:
            parcela_cent = getattr(contract, "parcela_cent", None)
            parcelas_restantes = getattr(contract, "parcelas_restantes", None)
            taxa_juros = getattr(contract, "taxa_juros", None)
            contract_id = getattr(contract, "contract_id", None) or "sem-id"
            lender_name = getattr(contract, "lender_name", None) or "Banco não identificado"

            if parcela_cent is None or parcelas_restantes is None or parcelas_restantes <= 0:
                continue

            taxa_atual_decimal = self._parse_percent_to_decimal(taxa_juros)
            if taxa_atual_decimal is None or taxa_atual_decimal <= 0:
                continue

            n = Decimal(parcelas_restantes)
            parcela_atual = self._to_decimal_cent(parcela_cent)

            # PV = parcela * (1 - (1 + i)^-n) / i
            pv = parcela_atual * (
                (Decimal("1") - (Decimal("1") + taxa_atual_decimal) ** (-n))
                / taxa_atual_decimal
            )

            # nova_parcela = PV * i_ref / (1 - (1 + i_ref)^-n)
            denominator = Decimal("1") - (Decimal("1") + taxa_ref_decimal) ** (-n)
            if denominator == 0:
                continue
            nova_parcela = pv * taxa_ref_decimal / denominator

            economia_mensal = parcela_atual - nova_parcela
            if economia_mensal <= 0:
                continue

            economia_total = economia_mensal * n
            nova_parcela_cent = self._to_cent(nova_parcela)
            economia_mensal_cent = self._to_cent(economia_mensal)
            economia_total_cent = self._to_cent(economia_total)

            simulations.append(
                SavingsContractSimulation(
                    contract_key=str(contract_id),
                    lender_name=lender_name,
                    parcela_atual_cent=parcela_cent,
                    parcela_nova_estimada_cent=nova_parcela_cent,
                    economia_mensal_cent=economia_mensal_cent,
                    economia_total_restante_cent=economia_total_cent,
                    parcelas_restantes=parcelas_restantes,
                    taxa_atual_mensal_percent=taxa_juros or "--",
                    taxa_referencia_mensal_percent=taxa_ref_percent,
                )
            )

        economia_mensal_total_cent = sum(item.economia_mensal_cent for item in simulations)
        economia_total_restante_cent = sum(
            item.economia_total_restante_cent for item in simulations
        )
        disclaimer = (
            f"Estimativa com taxa de referência de {taxa_ref_percent} a.m. "
            "Valores reais dependem de análise individual e negociação com a instituição financeira."
        )

        return SavingsSimulationResult(
            contratos=simulations,
            economia_mensal_total_cent=economia_mensal_total_cent,
            economia_total_restante_cent=economia_total_restante_cent,
            taxa_referencia_mensal_percent=taxa_ref_percent,
            disclaimer=disclaimer,
        )
