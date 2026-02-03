import pytest

from app.schemas.analysis_job import AnalysisJobCreate


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("3000", "3000.00"),
        ("3.000", "3000.00"),
        ("3.000,50", "3000.50"),
        ("3000.50", "3000.50"),
        ("1.234.567,89", "1234567.89"),
        ("1.234.567", "1234567.00"),
    ],
)
def test_validate_monetary_value_normalization(raw: str, expected: str) -> None:
    job = AnalysisJobCreate(
        renda_mensal_declarada=raw,
        gasto_dividas_declarado=raw,
    )

    assert job.renda_mensal_declarada == expected
    assert job.gasto_dividas_declarado == expected
