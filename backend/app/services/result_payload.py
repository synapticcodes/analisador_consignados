"""
Helpers para sanitização e montagem segura do payload de resultado.
"""

import re

from app.models.inss_margin import INSSMargin


def sanitize_pii_text(raw: str | None) -> str:
    """Sanitiza textos de evidência para reduzir exposição de PII."""
    if not raw:
        return ""
    text = raw
    text = re.sub(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", "***.***.***-**", text)
    text = re.sub(r"\b\d{10,14}\b", "************", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:300]


def truncate_alerts(alerts: list[str] | None, limit: int = 50) -> list[str]:
    if not alerts:
        return []
    return [alert[:limit] for alert in alerts]


def has_inss_margin_data(margin: INSSMargin | None) -> bool:
    if margin is None:
        return False
    return any(
        value is not None
        for value in (
            margin.base_calculo_cent,
            margin.max_comprometimento_cent,
            margin.total_comprometido_cent,
            margin.margem_emprestimo_cent,
            margin.margem_rmc_cent,
            margin.margem_rcc_cent,
            margin.cet_mensal,
            margin.cet_anual,
            margin.rmc_banco,
            margin.rmc_limite_cent,
            margin.rmc_reservado_cent,
        )
    )
