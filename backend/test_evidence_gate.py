#!/usr/bin/env python3
"""
Teste do Evidence Gate (Validação Determinística).
"""

import sys


def test_currency_parser():
    """Testa o parser de valores BR."""
    from app.services.evidence_gate import BrazilianCurrencyParser

    print("=" * 60)
    print("Teste 1: Brazilian Currency Parser")
    print("=" * 60)

    parser = BrazilianCurrencyParser()

    # Casos de teste (formato, valor esperado)
    test_cases = [
        ("R$ 1.334,36", 1334.36),
        ("1.334,36", 1334.36),
        ("1334,36", 1334.36),
        ("R$ 5.500,00", 5500.00),
        ("Total: R$ 4.115,00", 4115.00),
        ("Líquido: 3.800", 3800.00),
        ("250,00", 250.00),
        ("R$180,50", 180.50),
        ("R$ 10.000,00", 10000.00),
    ]

    all_passed = True
    for i, (text, expected) in enumerate(test_cases, 1):
        result = parser.parse(text)
        passed = result is not None and abs(result - expected) < 0.01

        status = "✅" if passed else "❌"
        print(f"\n{i}. {status} '{text}'")
        print(f"   Esperado: {expected:.2f}")
        if result is not None:
            print(f"   Obtido: {result:.2f}")
        else:
            print("   Obtido: None")

        if not passed:
            all_passed = False

    return all_passed


def test_evidence_gate_with_valid_data():
    """Testa Evidence Gate com dados válidos (deve passar)."""
    from app.services.evidence_gate import EvidenceGate
    from app.services.extractors import (
        ConsignadoLine,
        ExtractedField,
        FieldEvidence,
        PaymentExtractionResult,
    )

    print("\n" + "=" * 60)
    print("Teste 2: Evidence Gate - Dados Válidos")
    print("=" * 60)

    # Criar resultado de extração com evidências corretas
    result = PaymentExtractionResult(
        competencia="2024-01",
        salario_bruto=ExtractedField(
            value=5500.00,
            currency="BRL",
            method="EXTRACTED",
            evidence=FieldEvidence(
                page=0, text="Total de Proventos: R$ 5.500,00"
            ),
        ),
        salario_liquido=ExtractedField(
            value=4115.00,
            currency="BRL",
            method="EXTRACTED",
            evidence=FieldEvidence(page=0, text="Líquido: R$ 4.115,00"),
        ),
        total_descontos=ExtractedField(
            value=1385.00,
            currency="BRL",
            method="EXTRACTED",
            evidence=FieldEvidence(page=0, text="Descontos: R$ 1.385,00"),
        ),
        linhas_consignado=[
            ConsignadoLine(
                descricao="Banco ABC",
                rubrica="216",
                valor_cent=25000,
                evidence=FieldEvidence(page=0, text="Consignado: R$ 250,00"),
            )
        ],
        alerts=[],
    )

    # Validar
    gate = EvidenceGate(tolerance=0.01)
    gate_result = gate.validate_payment_extraction(result)

    print(f"\n📊 Status: {gate_result.gate_status.value}")
    print(f"✅ Campos validados: {gate_result.validated_fields}")
    print(f"❌ Campos falhos: {gate_result.failed_fields}")
    print(f"⚠️  Alertas: {len(gate_result.alerts)}")

    if gate_result.alerts:
        print("\nAlertas encontrados:")
        for alert in gate_result.alerts:
            print(f"  - {alert.field_name}: {alert.reason}")

    # Check
    passed = gate_result.gate_status.value == "PASSED" and len(gate_result.alerts) == 0
    print(f"\n{'✅' if passed else '❌'} Gate deve PASSAR com dados válidos")

    return passed


def test_evidence_gate_with_divergent_data():
    """Testa Evidence Gate com dados divergentes (deve falhar)."""
    from app.services.evidence_gate import EvidenceGate
    from app.services.extractors import ExtractedField, FieldEvidence, PaymentExtractionResult

    print("\n" + "=" * 60)
    print("Teste 3: Evidence Gate - Dados Divergentes")
    print("=" * 60)

    # Criar resultado com valor extraído diferente da evidência
    result = PaymentExtractionResult(
        competencia="2024-01",
        salario_bruto=ExtractedField(
            value=9999.99,  # Valor ERRADO (evidência diz 5.500,00)
            currency="BRL",
            method="EXTRACTED",
            evidence=FieldEvidence(
                page=0, text="Total de Proventos: R$ 5.500,00"
            ),
        ),
        salario_liquido=ExtractedField(
            value=4115.00,
            currency="BRL",
            method="EXTRACTED",
            evidence=FieldEvidence(page=0, text="Líquido: R$ 4.115,00"),
        ),
        total_descontos=ExtractedField(value=None, currency=None, method=None, evidence=None),
        linhas_consignado=[],
        alerts=[],
    )

    # Validar
    gate = EvidenceGate(tolerance=0.01)
    gate_result = gate.validate_payment_extraction(result)

    print(f"\n📊 Status: {gate_result.gate_status.value}")
    print(f"✅ Campos validados: {gate_result.validated_fields}")
    print(f"❌ Campos falhos: {gate_result.failed_fields}")
    print(f"⚠️  Alertas: {len(gate_result.alerts)}")

    if gate_result.alerts:
        print("\nAlertas encontrados:")
        for alert in gate_result.alerts:
            crit = " [CRÍTICO]" if alert.is_critical else ""
            print(f"  - {alert.field_name}{crit}: {alert.reason}")
            print(f"    Extraído: {alert.extracted_value}, Re-parseado: {alert.reparsed_value}")

    # Check
    passed = gate_result.gate_status.value == "FAILED" and len(gate_result.alerts) > 0
    print(f"\n{'✅' if passed else '❌'} Gate deve FALHAR com dados divergentes")

    return passed


def test_evidence_gate_invariants():
    """Testa validação de invariantes matemáticos."""
    from app.services.evidence_gate import EvidenceGate
    from app.services.extractors import ExtractedField, FieldEvidence, PaymentExtractionResult

    print("\n" + "=" * 60)
    print("Teste 4: Evidence Gate - Invariantes Matemáticos")
    print("=" * 60)

    # Criar resultado com invariante violado (bruto < liquido)
    result = PaymentExtractionResult(
        competencia="2024-01",
        salario_bruto=ExtractedField(
            value=3000.00,  # MENOR que líquido (violação!)
            currency="BRL",
            method="EXTRACTED",
            evidence=FieldEvidence(page=0, text="Proventos: R$ 3.000,00"),
        ),
        salario_liquido=ExtractedField(
            value=4115.00,  # MAIOR que bruto (violação!)
            currency="BRL",
            method="EXTRACTED",
            evidence=FieldEvidence(page=0, text="Líquido: R$ 4.115,00"),
        ),
        total_descontos=ExtractedField(
            value=-100.00,  # NEGATIVO (violação!)
            currency="BRL",
            method="EXTRACTED",
            evidence=FieldEvidence(page=0, text="Descontos: R$ -100,00"),
        ),
        linhas_consignado=[],
        alerts=[],
    )

    # Validar
    gate = EvidenceGate(tolerance=0.01)
    gate_result = gate.validate_payment_extraction(result)

    print(f"\n📊 Status: {gate_result.gate_status.value}")
    print(f"⚠️  Alertas: {len(gate_result.alerts)}")

    if gate_result.alerts:
        print("\nInvariantes violados:")
        for alert in gate_result.alerts:
            if "invariant" in alert.field_name:
                crit = " [CRÍTICO]" if alert.is_critical else ""
                print(f"  - {alert.field_name}{crit}: {alert.reason}")

    # Checks
    has_invariant_alert = any("invariant" in a.field_name for a in gate_result.alerts)
    is_failed = gate_result.gate_status.value == "FAILED"

    passed = has_invariant_alert and is_failed
    print(f"\n{'✅' if passed else '❌'} Gate deve detectar invariantes violados")

    return passed


def test_evidence_gate_missing_evidence():
    """Testa Evidence Gate com evidência ausente."""
    from app.services.evidence_gate import EvidenceGate
    from app.services.extractors import ExtractedField, PaymentExtractionResult

    print("\n" + "=" * 60)
    print("Teste 5: Evidence Gate - Evidência Ausente")
    print("=" * 60)

    # Criar resultado sem evidência
    result = PaymentExtractionResult(
        competencia="2024-01",
        salario_bruto=ExtractedField(
            value=5500.00,
            currency="BRL",
            method="EXTRACTED",
            evidence=None,  # SEM EVIDÊNCIA!
        ),
        salario_liquido=ExtractedField(
            value=4115.00,
            currency="BRL",
            method="EXTRACTED",
            evidence=None,  # SEM EVIDÊNCIA!
        ),
        total_descontos=ExtractedField(value=None, currency=None, method=None, evidence=None),
        linhas_consignado=[],
        alerts=[],
    )

    # Validar
    gate = EvidenceGate(tolerance=0.01)
    gate_result = gate.validate_payment_extraction(result)

    print(f"\n📊 Status: {gate_result.gate_status.value}")
    print(f"⚠️  Alertas: {len(gate_result.alerts)}")

    if gate_result.alerts:
        print("\nAlertas de evidência ausente:")
        for alert in gate_result.alerts:
            print(f"  - {alert.field_name}: {alert.reason}")

    # Check
    passed = (
        gate_result.gate_status.value == "FAILED"
        and len(gate_result.alerts) >= 2  # Ambos campos críticos sem evidência
    )
    print(f"\n{'✅' if passed else '❌'} Gate deve rejeitar valores sem evidência")

    return passed


def main():
    """Executa todos os testes."""
    try:
        # Teste 1: Parser de moeda BR
        result1 = test_currency_parser()

        # Teste 2: Dados válidos
        result2 = test_evidence_gate_with_valid_data()

        # Teste 3: Dados divergentes
        result3 = test_evidence_gate_with_divergent_data()

        # Teste 4: Invariantes matemáticos
        result4 = test_evidence_gate_invariants()

        # Teste 5: Evidência ausente
        result5 = test_evidence_gate_missing_evidence()

        # Resultado final
        print("\n" + "=" * 60)
        all_passed = result1 and result2 and result3 and result4 and result5
        if all_passed:
            print("✅ Todos os testes do Evidence Gate passaram!")
        else:
            print("❌ Alguns testes falharam")
        print("=" * 60)

        return all_passed

    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
