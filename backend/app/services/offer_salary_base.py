"""
Resolução de base salarial para geração de ofertas.
"""

from typing import Any

MIN_OFFER_QUALIFICATION_CENT = 1621 * 100


def _as_positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, float) and value.is_integer():
        int_value = int(value)
        return int_value if int_value > 0 else None
    return None


def estimate_beneficio_liquido_cent(
    inss_margin_data: dict[str, object] | None,
) -> int | None:
    """
    Estima benefício líquido em centavos.

    Fórmula: benefício líquido = base de cálculo - total comprometido.
    """
    if not inss_margin_data:
        return None

    base_calculo = _as_positive_int(inss_margin_data.get("base_calculo_cent"))
    total_comprometido = _as_positive_int(
        inss_margin_data.get("total_comprometido_cent")
    )
    if base_calculo is None or total_comprometido is None:
        return None

    beneficio_liquido = base_calculo - total_comprometido
    if beneficio_liquido <= 0:
        return None
    return beneficio_liquido


def resolve_offer_salary_cent(
    compute_salario_liquido_cent: int | None,
    renda_mensal_declarada_cent: int | None,
    perfil_dados: str | None,
    inss_margin_data: dict[str, object] | None = None,
) -> tuple[int | None, str]:
    """
    Resolve a base para geração de ofertas.

    Prioridade:
    1. salário líquido calculado (>0)
    2. benefício líquido estimado do extrato (EXTRATO_ONLY)
    3. renda declarada (>0)
    """
    salario_liquido = _as_positive_int(compute_salario_liquido_cent)
    if salario_liquido is not None:
        return salario_liquido, "SALARIO_LIQUIDO"

    if perfil_dados == "EXTRATO_ONLY":
        beneficio_liquido = estimate_beneficio_liquido_cent(inss_margin_data)
        if beneficio_liquido is not None:
            return beneficio_liquido, "BENEFICIO_LIQUIDO_EXTRATO"

    renda_declarada = _as_positive_int(renda_mensal_declarada_cent)
    if renda_declarada is not None:
        return renda_declarada, "RENDA_DECLARADA"

    return None, "INDISPONIVEL"


def resolve_offer_qualification_base_cent(
    compute_salario_liquido_cent: int | None,
    perfil_dados: str | None,
    inss_margin_data: dict[str, object] | None = None,
) -> tuple[int | None, str]:
    """
    Resolve a base de elegibilidade para ofertas.

    Regras:
    - EXTRATO_ONLY: usa benefício líquido.
    - PAYROLL_AND_EXTRATO: usa salário líquido + benefício líquido quando ambos existem.
    - Demais perfis: usa salário líquido.
    """
    salario_liquido = _as_positive_int(compute_salario_liquido_cent)
    beneficio_liquido = estimate_beneficio_liquido_cent(inss_margin_data)

    if perfil_dados == "EXTRATO_ONLY":
        if beneficio_liquido is not None:
            return beneficio_liquido, "BENEFICIO_LIQUIDO_EXTRATO"
        return None, "INDISPONIVEL"

    if perfil_dados == "PAYROLL_AND_EXTRATO":
        if salario_liquido is not None and beneficio_liquido is not None:
            return salario_liquido + beneficio_liquido, "SALARIO_MAIS_BENEFICIO"
        if salario_liquido is not None:
            return salario_liquido, "SALARIO_LIQUIDO"
        if beneficio_liquido is not None:
            return beneficio_liquido, "BENEFICIO_LIQUIDO_EXTRATO"
        return None, "INDISPONIVEL"

    if salario_liquido is not None:
        return salario_liquido, "SALARIO_LIQUIDO"
    if beneficio_liquido is not None:
        return beneficio_liquido, "BENEFICIO_LIQUIDO_EXTRATO"
    return None, "INDISPONIVEL"


def is_offer_qualified(
    compute_salario_liquido_cent: int | None,
    perfil_dados: str | None,
    inss_margin_data: dict[str, object] | None = None,
    *,
    min_qualification_cent: int = MIN_OFFER_QUALIFICATION_CENT,
) -> tuple[bool, int | None, str]:
    """
    Determina se o lead se qualifica para ofertas.
    """
    base_cent, source = resolve_offer_qualification_base_cent(
        compute_salario_liquido_cent=compute_salario_liquido_cent,
        perfil_dados=perfil_dados,
        inss_margin_data=inss_margin_data,
    )
    if base_cent is None:
        return True, None, source
    return base_cent >= min_qualification_cent, base_cent, source
