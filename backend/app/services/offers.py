"""
Offer generation service
"""

from dataclasses import dataclass
import math
import random
from typing import Iterable
from uuid import UUID

from app.models.offer import OfferKind
from app.models.product import Product

RENDA_FAIXA_A_CENT = 3500 * 100
RENDA_FAIXA_B_CENT = 2500 * 100

PERCENT_RANGES_BY_FAIXA: dict[str, dict[str, tuple[int, int]]] = {
    "A": {
        OfferKind.PRINCIPAL.value: (4, 6),
        OfferKind.REDUZIDA.value: (5, 7),
        OfferKind.SUPER.value: (8, 11),
    },
    "B": {
        OfferKind.PRINCIPAL.value: (5, 6),
        OfferKind.REDUZIDA.value: (6, 7),
        OfferKind.SUPER.value: (7, 8),
    },
}

PERCENT_RANGE_FAIXA_C = (7, 9)
ENTRY_PERCENT_RANGE_FAIXA_C = (5, 10)

DUE_RANGES_BY_FAIXA: dict[str, dict[str, tuple[int, int]]] = {
    "A": {
        OfferKind.PRINCIPAL.value: (21, 30),
        OfferKind.REDUZIDA.value: (7, 15),
        OfferKind.SUPER.value: (1, 7),
    },
    "B": {
        OfferKind.PRINCIPAL.value: (14, 21),
        OfferKind.REDUZIDA.value: (10, 14),
        OfferKind.SUPER.value: (7, 9),
    },
}

DUE_RANGE_FAIXA_C = (10, 15)

TOTAL_VARIATION_BY_KIND: dict[str, int] = {
    OfferKind.PRINCIPAL.value: 25,
    OfferKind.REDUZIDA.value: 20,
    OfferKind.SUPER.value: 15,
}

INSTALLMENT_RATIO_BY_KIND: dict[str, tuple[float, float]] = {
    OfferKind.SUPER.value: (0.20, 0.35),
    OfferKind.REDUZIDA.value: (0.55, 0.75),
    OfferKind.PRINCIPAL.value: (1.0, 1.0),
}

INSTALLMENT_MIN = 6
INSTALLMENT_MAX = 24
MAX_INSTALLMENTS_FAIXA_A = 36
MAX_INSTALLMENTS_FAIXA_B = 18
ALLOWED_PAYMENT_METHODS = {"PIX", "BOLETO"}
SUPER_ALLOWED_INSTALLMENTS_FAIXA_C = {6, 8}


@dataclass
class OfferDraft:
    kind: str
    installment_count: int
    installment_value_cent: int
    total_value_cent: int
    first_payment_days: int
    payment_method: str
    salary_liquid_used_cent: int
    percent_used: int
    text: str
    entry_value_cent: int | None = None
    entry_due_days: int | None = None


@dataclass
class OfferCandidate:
    installment_count: int
    installment_value_cent: int
    total_value_cent: int
    percent_used: int
    diff_installment: int
    diff_total: int


def _format_brl_from_cents(value_cent: int) -> str:
    reais = value_cent // 100
    centavos = value_cent % 100
    reais_fmt = f"{reais:,}".replace(",", ".")
    return f"R$ {reais_fmt},{centavos:02d}"


def _normalize_payment_methods(methods: Iterable[str]) -> list[str]:
    normalized = [item.strip().upper() for item in methods if item]
    return [item for item in normalized if item in ALLOWED_PAYMENT_METHODS]


def _income_band(salary_cent: int) -> str:
    if salary_cent >= RENDA_FAIXA_A_CENT:
        return "A"
    if salary_cent >= RENDA_FAIXA_B_CENT:
        return "B"
    return "C"


def _max_allowed_days(range_min: int, range_max: int, installment_count: int) -> int:
    if range_max <= range_min:
        return range_min
    span = INSTALLMENT_MAX - INSTALLMENT_MIN
    if span <= 0:
        return range_min
    factor = (installment_count - INSTALLMENT_MIN) / span
    if factor < 0:
        factor = 0
    elif factor > 1:
        factor = 1
    return range_min + int(round(factor * (range_max - range_min)))


def _installment_bounds(
    max_installments: int,
    min_pct: float,
    max_pct: float,
) -> tuple[int, int]:
    min_count = int(math.ceil(max_installments * min_pct))
    max_count = int(math.floor(max_installments * max_pct))
    if min_count < INSTALLMENT_MIN:
        min_count = INSTALLMENT_MIN
    if max_count < min_count:
        max_count = min_count
    return min_count, max_count


def _allowed_installments(
    installments: list[int],
    max_installments: int,
    kind: str,
) -> list[int]:
    min_pct, max_pct = INSTALLMENT_RATIO_BY_KIND[kind]
    min_count, max_count = _installment_bounds(max_installments, min_pct, max_pct)
    allowed = [count for count in sorted(set(installments)) if min_count <= count <= max_count]
    return allowed


def _generate_candidates(
    salary_cent: int,
    percent_min: int,
    percent_max: int,
    installments: list[int],
    base_value_cent: int,
    total_variation_percent: int,
    *,
    clamp_total: bool = True,
    hard_max_percent: int | None = None,
) -> list[OfferCandidate]:
    min_total = (base_value_cent * (100 - total_variation_percent)) // 100
    max_total = (base_value_cent * (100 + total_variation_percent)) // 100

    candidates: list[OfferCandidate] = []
    for percent_used in range(percent_min, percent_max + 1):
        target_installment = (salary_cent * percent_used) // 100
        for count in installments:
            clamped_total = target_installment * count
            if clamp_total:
                if clamped_total < min_total:
                    clamped_total = min_total
                elif clamped_total > max_total:
                    clamped_total = max_total

            installment_value = clamped_total // count
            if installment_value <= 0:
                continue

            actual_total = installment_value * count
            if installment_value * 100 < percent_min * salary_cent:
                continue
            if installment_value * 100 > percent_max * salary_cent:
                continue
            if hard_max_percent is not None and installment_value * 100 > hard_max_percent * salary_cent:
                continue
            diff_installment = abs(installment_value - target_installment)
            diff_total = abs(actual_total - base_value_cent)
            candidates.append(
                OfferCandidate(
                    installment_count=count,
                    installment_value_cent=installment_value,
                    total_value_cent=actual_total,
                    percent_used=percent_used,
                    diff_installment=diff_installment,
                    diff_total=diff_total,
                )
            )

    candidates.sort(
        key=lambda candidate: (
            candidate.diff_installment,
            candidate.diff_total,
            candidate.installment_count,
            candidate.percent_used,
        )
    )
    return candidates


def _resolve_due_days(
    ranges_by_kind: dict[str, tuple[int, int]],
    principal_count: int,
    reduzida_count: int,
    super_count: int,
) -> tuple[int, int, int] | None:
    p_min, p_max = ranges_by_kind[OfferKind.PRINCIPAL.value]
    r_min, r_max = ranges_by_kind[OfferKind.REDUZIDA.value]
    s_min, s_max = ranges_by_kind[OfferKind.SUPER.value]

    due_principal = _max_allowed_days(p_min, p_max, principal_count)

    max_reduzida = _max_allowed_days(r_min, r_max, reduzida_count)
    mid_reduzida = r_min + (r_max - r_min) // 2
    due_reduzida = min(max_reduzida, mid_reduzida)
    if due_reduzida >= due_principal:
        due_reduzida = min(max_reduzida, due_principal - 1)
    if due_reduzida < r_min:
        return None

    max_super = _max_allowed_days(s_min, s_max, super_count)
    due_super = min(max_super, due_reduzida - 1)
    if due_super < s_min:
        return None

    if not (due_super < due_reduzida < due_principal):
        return None
    return due_principal, due_reduzida, due_super


def _select_bundle(
    candidates_by_kind: dict[str, list[OfferCandidate]],
    ranges_by_kind: dict[str, tuple[int, int]],
    require_total_order: bool,
) -> tuple[dict[str, OfferCandidate], tuple[int, int, int]] | None:
    principal_list = candidates_by_kind.get(OfferKind.PRINCIPAL.value) or []
    reduzida_list = candidates_by_kind.get(OfferKind.REDUZIDA.value) or []
    super_list = candidates_by_kind.get(OfferKind.SUPER.value) or []

    for principal in principal_list:
        for reduzida in reduzida_list:
            if reduzida.installment_value_cent <= principal.installment_value_cent:
                continue
            if require_total_order and reduzida.total_value_cent >= principal.total_value_cent:
                continue
            if reduzida.installment_count >= principal.installment_count:
                continue
            for super_offer in super_list:
                if super_offer.installment_value_cent <= reduzida.installment_value_cent:
                    continue
                if require_total_order and super_offer.total_value_cent >= reduzida.total_value_cent:
                    continue
                if super_offer.installment_count >= reduzida.installment_count:
                    continue

                due_days = _resolve_due_days(
                    ranges_by_kind,
                    principal.installment_count,
                    reduzida.installment_count,
                    super_offer.installment_count,
                )
                if due_days is None:
                    continue

                return (
                    {
                        OfferKind.PRINCIPAL.value: principal,
                        OfferKind.REDUZIDA.value: reduzida,
                        OfferKind.SUPER.value: super_offer,
                    },
                    due_days,
                )
    return None


def _build_candidates_for_kind(
    kind: str,
    salary_cent: int,
    base_value_cent: int,
    installments: list[int],
    percent_range: tuple[int, int],
    *,
    clamp_total: bool,
    hard_max_percent: int | None = None,
) -> list[OfferCandidate]:
    percent_min, percent_max = percent_range
    return _generate_candidates(
        salary_cent=salary_cent,
        percent_min=percent_min,
        percent_max=percent_max,
        installments=installments,
        base_value_cent=base_value_cent,
        total_variation_percent=TOTAL_VARIATION_BY_KIND[kind],
        clamp_total=clamp_total,
        hard_max_percent=hard_max_percent,
    )


def _fallback_installment(installments: list[int], pick_max: bool) -> list[int]:
    if not installments:
        return []
    return [max(installments) if pick_max else min(installments)]


def generate_offers(
    job_id: UUID,
    salary_cent: int | None,
    product: Product,
) -> tuple[list[OfferDraft], list[str]]:
    alerts: list[str] = []

    if salary_cent is None or salary_cent <= 0:
        alerts.append("Ofertas não geradas: salário líquido indisponível")
        return [], alerts

    payment_methods = _normalize_payment_methods(product.payment_methods or [])
    if not payment_methods:
        alerts.append("Ofertas não geradas: formas de pagamento inválidas")
        return [], alerts

    if not product.installments:
        alerts.append("Ofertas não geradas: parcelamentos inválidos")
        return [], alerts

    faixa = _income_band(salary_cent)

    if faixa == "C":
        installments = [
            count
            for count in sorted(set(product.installments))
            if count in SUPER_ALLOWED_INSTALLMENTS_FAIXA_C
        ]
        if not installments:
            alerts.append("Faixa C: parcelamentos 6x/8x indisponíveis, usando fallback")
            installments = _fallback_installment(sorted(set(product.installments)), pick_max=False)

        percent_min, percent_max = PERCENT_RANGE_FAIXA_C
        rng = random.Random(f"{job_id}:faixa-c")
        percent_used = rng.randint(percent_min, percent_max)
        installment_count = rng.choice(installments)
        installment_value_cent = (salary_cent * percent_used) // 100
        if installment_value_cent <= 0:
            alerts.append("Ofertas não geradas: faixa C com parcela inválida")
            return [], alerts

        total_value_cent = installment_value_cent * installment_count
        selected = OfferCandidate(
            installment_count=installment_count,
            installment_value_cent=installment_value_cent,
            total_value_cent=total_value_cent,
            percent_used=percent_used,
            diff_installment=0,
            diff_total=0,
        )
        due_min, due_max = DUE_RANGE_FAIXA_C
        max_allowed = _max_allowed_days(due_min, due_max, selected.installment_count)
        due_mid = due_min + (due_max - due_min) // 2
        first_payment_days = min(max_allowed, due_mid)
        if first_payment_days < due_min:
            first_payment_days = due_min

        entry_percent = random.Random(f"{job_id}:entry").randint(
            ENTRY_PERCENT_RANGE_FAIXA_C[0], ENTRY_PERCENT_RANGE_FAIXA_C[1]
        )
        entry_value_cent = (salary_cent * entry_percent) // 100
        entry_due_days = 1

        payment_method = random.Random(f"{job_id}:single:payment").choice(payment_methods)
        method_label = "PIX" if payment_method == "PIX" else "boleto"
        installment_label = _format_brl_from_cents(selected.installment_value_cent)
        entry_label = _format_brl_from_cents(entry_value_cent)
        text = (
            f"Entrada de {entry_label} em {entry_due_days} dia(s) + "
            f"{selected.installment_count}x de {installment_label} no {method_label}, "
            f"1ª parcela em {first_payment_days} dias"
        )

        return (
            [
                OfferDraft(
                    kind=OfferKind.REDUZIDA.value,
                    installment_count=selected.installment_count,
                    installment_value_cent=selected.installment_value_cent,
                    total_value_cent=selected.total_value_cent,
                    first_payment_days=first_payment_days,
                    payment_method=payment_method,
                    salary_liquid_used_cent=salary_cent,
                    percent_used=selected.percent_used,
                    text=text,
                    entry_value_cent=entry_value_cent,
                    entry_due_days=entry_due_days,
                )
            ],
            alerts,
        )

    ranges_by_kind = PERCENT_RANGES_BY_FAIXA[faixa]
    due_ranges = DUE_RANGES_BY_FAIXA[faixa]

    max_installments = max(product.installments)
    max_cap = MAX_INSTALLMENTS_FAIXA_A if faixa == "A" else MAX_INSTALLMENTS_FAIXA_B
    max_effective = min(max_installments, max_cap)
    principal_installments = [count for count in sorted(set(product.installments)) if count <= max_effective]
    if principal_installments:
        principal_installments = [max(principal_installments)]
    else:
        alerts.append("Parcelamento máximo indisponível, usando fallback")
        principal_installments = _fallback_installment(sorted(set(product.installments)), pick_max=True)

    reduzida_installments = _allowed_installments(
        installments=product.installments,
        max_installments=max_effective,
        kind=OfferKind.REDUZIDA.value,
    )
    if not reduzida_installments:
        alerts.append("Faixa %s: reduzida fora do range, usando fallback" % faixa)
        reduzida_installments = [count for count in sorted(set(product.installments)) if count < principal_installments[0]]
        if not reduzida_installments:
            reduzida_installments = _fallback_installment(sorted(set(product.installments)), pick_max=False)

    super_installments = _allowed_installments(
        installments=product.installments,
        max_installments=max_effective,
        kind=OfferKind.SUPER.value,
    )
    if not super_installments:
        alerts.append("Faixa %s: super fora do range, usando fallback" % faixa)
        super_installments = [count for count in sorted(set(product.installments)) if count < min(reduzida_installments)]
        if not super_installments:
            super_installments = _fallback_installment(sorted(set(product.installments)), pick_max=False)

    candidates_by_kind: dict[str, list[OfferCandidate]] = {}
    for kind, allowed_installments in (
        (OfferKind.PRINCIPAL.value, principal_installments),
        (OfferKind.REDUZIDA.value, reduzida_installments),
        (OfferKind.SUPER.value, super_installments),
    ):
        percent_range = ranges_by_kind[kind]
        hard_max_percent = 12 if kind == OfferKind.SUPER.value else None
        candidates = _build_candidates_for_kind(
            kind=kind,
            salary_cent=salary_cent,
            base_value_cent=product.base_value_cent,
            installments=allowed_installments,
            percent_range=percent_range,
            clamp_total=True,
            hard_max_percent=hard_max_percent,
        )
        if not candidates:
            alerts.append(
                f"Faixa {faixa}: {kind.lower()} sem candidatos no preço base, usando renda"
            )
            candidates = _build_candidates_for_kind(
                kind=kind,
                salary_cent=salary_cent,
                base_value_cent=product.base_value_cent,
                installments=allowed_installments,
                percent_range=percent_range,
                clamp_total=False,
                hard_max_percent=hard_max_percent,
            )
        candidates_by_kind[kind] = candidates

    selection = _select_bundle(candidates_by_kind, due_ranges, require_total_order=True)
    if not selection:
        selection = _select_bundle(candidates_by_kind, due_ranges, require_total_order=False)
        if not selection:
            alerts.append(
                "Ofertas não geradas: não foi possível respeitar a hierarquia final"
            )
            return [], alerts
        alerts.append(
            "Ofertas geradas sem hierarquia de total (renda baixa)"
        )

    selected_by_kind, due_days = selection
    due_principal, due_reduzida, due_super = due_days
    days_by_kind = {
        OfferKind.PRINCIPAL.value: due_principal,
        OfferKind.REDUZIDA.value: due_reduzida,
        OfferKind.SUPER.value: due_super,
    }

    offers: list[OfferDraft] = []
    for kind in [OfferKind.PRINCIPAL.value, OfferKind.REDUZIDA.value, OfferKind.SUPER.value]:
        selected = selected_by_kind.get(kind)
        if not selected:
            continue
        payment_method = random.Random(f"{job_id}:{kind}:payment").choice(payment_methods)
        first_payment_days = days_by_kind.get(kind)
        if first_payment_days is None:
            first_payment_days = random.Random(f"{job_id}:{kind}:days").choice(
                FIRST_PAYMENT_DAYS
            )

        method_label = "PIX" if payment_method == "PIX" else "boleto"
        installment_label = _format_brl_from_cents(selected.installment_value_cent)
        text = (
            f"{selected.installment_count}x de {installment_label} no {method_label}, "
            f"1ª parcela em {first_payment_days} dias"
        )

        offers.append(
            OfferDraft(
                kind=kind,
                installment_count=selected.installment_count,
                installment_value_cent=selected.installment_value_cent,
                total_value_cent=selected.total_value_cent,
                first_payment_days=first_payment_days,
                payment_method=payment_method,
                salary_liquid_used_cent=salary_cent,
                percent_used=selected.percent_used,
                text=text,
            )
        )

    return offers, alerts
