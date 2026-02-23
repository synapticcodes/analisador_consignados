from types import SimpleNamespace
from uuid import UUID

import pytest

from app.services.offers import generate_offers


def _build_product(
    *,
    payment_methods: list[str] | None = None,
):
    return SimpleNamespace(
        base_value_cent=1_000_000,
        installments=[6, 8, 12, 18, 24, 36],
        payment_methods=payment_methods if payment_methods is not None else ["PIX", "BOLETO"],
    )


@pytest.mark.unit
def test_generate_offers_faixa_a_forca_boleto_em_todas_as_ofertas():
    job_id = UUID("11111111-1111-1111-1111-111111111111")
    product = _build_product()

    offers, _alerts = generate_offers(
        job_id=job_id,
        salary_cent=400_000,
        product=product,
    )

    assert len(offers) == 3
    assert all(offer.payment_method == "BOLETO" for offer in offers)
    assert all("no boleto" in offer.text.lower() for offer in offers)


@pytest.mark.unit
def test_generate_offers_faixa_c_usa_entrada_pix_e_parcelas_boleto():
    job_id = UUID("22222222-2222-2222-2222-222222222222")
    product = _build_product()

    offers, _alerts = generate_offers(
        job_id=job_id,
        salary_cent=180_000,
        product=product,
    )

    assert len(offers) == 1
    offer = offers[0]
    assert offer.payment_method == "BOLETO"
    assert offer.entry_value_cent is not None
    assert "via PIX" in offer.text
    assert "no boleto" in offer.text.lower()


@pytest.mark.unit
def test_generate_offers_ignora_formas_pagamento_produto_vazias():
    job_id = UUID("33333333-3333-3333-3333-333333333333")
    product = _build_product(payment_methods=[])

    offers, alerts = generate_offers(
        job_id=job_id,
        salary_cent=400_000,
        product=product,
    )

    assert len(offers) == 3
    assert all(offer.payment_method == "BOLETO" for offer in offers)
    assert "Ofertas não geradas: formas de pagamento inválidas" not in alerts
