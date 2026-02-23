import pytest

from app.services.offer_salary_base import (
    estimate_beneficio_liquido_cent,
    is_offer_qualified,
    resolve_offer_qualification_base_cent,
    resolve_offer_salary_cent,
)


@pytest.mark.unit
def test_estimate_beneficio_liquido_cent_quando_margem_valida():
    data = {
        "base_calculo_cent": 162100,
        "total_comprometido_cent": 61135,
    }

    assert estimate_beneficio_liquido_cent(data) == 100965


@pytest.mark.unit
def test_resolve_offer_salary_cent_prioriza_salario_liquido():
    salary_cent, source = resolve_offer_salary_cent(
        compute_salario_liquido_cent=350000,
        renda_mensal_declarada_cent=450000,
        perfil_dados="EXTRATO_ONLY",
        inss_margin_data={
            "base_calculo_cent": 162100,
            "total_comprometido_cent": 61135,
        },
    )

    assert salary_cent == 350000
    assert source == "SALARIO_LIQUIDO"


@pytest.mark.unit
def test_resolve_offer_salary_cent_usa_beneficio_liquido_no_extrato():
    salary_cent, source = resolve_offer_salary_cent(
        compute_salario_liquido_cent=0,
        renda_mensal_declarada_cent=None,
        perfil_dados="EXTRATO_ONLY",
        inss_margin_data={
            "base_calculo_cent": 162100,
            "total_comprometido_cent": 61135,
        },
    )

    assert salary_cent == 100965
    assert source == "BENEFICIO_LIQUIDO_EXTRATO"


@pytest.mark.unit
def test_resolve_offer_salary_cent_fallback_renda_declarada_sem_margem():
    salary_cent, source = resolve_offer_salary_cent(
        compute_salario_liquido_cent=0,
        renda_mensal_declarada_cent=420000,
        perfil_dados="EXTRATO_ONLY",
        inss_margin_data=None,
    )

    assert salary_cent == 420000
    assert source == "RENDA_DECLARADA"


@pytest.mark.unit
def test_resolve_offer_qualification_base_cent_soma_salario_e_beneficio_no_misto():
    base_cent, source = resolve_offer_qualification_base_cent(
        compute_salario_liquido_cent=120000,
        perfil_dados="PAYROLL_AND_EXTRATO",
        inss_margin_data={
            "base_calculo_cent": 80000,
            "total_comprometido_cent": 20000,
        },
    )

    assert base_cent == 180000
    assert source == "SALARIO_MAIS_BENEFICIO"


@pytest.mark.unit
def test_is_offer_qualified_false_quando_base_abaixo_do_minimo():
    qualified, base_cent, source = is_offer_qualified(
        compute_salario_liquido_cent=120000,
        perfil_dados="PAYROLL_ONLY",
        inss_margin_data=None,
    )

    assert qualified is False
    assert base_cent == 120000
    assert source == "SALARIO_LIQUIDO"
