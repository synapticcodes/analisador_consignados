#!/usr/bin/env python3
"""
Teste do Consolidator & Compute Engine.
"""

import sys


def test_competencia_selection():
    """Testa seleção de competência alvo (RF-008)."""
    from app.services.consolidator import ConsolidatorService, DocumentSource
    from app.services.extractors import (
        ExtractedField,
        FieldEvidence,
        PaymentExtractionResult,
    )

    print("=" * 60)
    print("Teste 1: Seleção de Competência Alvo")
    print("=" * 60)

    consolidator = ConsolidatorService()

    # Criar múltiplos resultados com competências diferentes
    results = [
        PaymentExtractionResult(
            competencia="01/2024",
            salario_bruto=ExtractedField(
                value=5000.0,
                currency="BRL",
                method="EXTRACTED",
                evidence=FieldEvidence(page=0, text="R$ 5.000,00"),
            ),
            salario_liquido=ExtractedField(
                value=4000.0,
                currency="BRL",
                method="EXTRACTED",
                evidence=FieldEvidence(page=0, text="R$ 4.000,00"),
            ),
            total_descontos=ExtractedField(
                value=None, currency=None, method=None, evidence=None
            ),
            linhas_consignado=[],
            alerts=[],
        ),
        PaymentExtractionResult(
            competencia="12/2023",  # Mais antiga
            salario_bruto=ExtractedField(
                value=4800.0,
                currency="BRL",
                method="EXTRACTED",
                evidence=FieldEvidence(page=0, text="R$ 4.800,00"),
            ),
            salario_liquido=ExtractedField(
                value=3900.0,
                currency="BRL",
                method="EXTRACTED",
                evidence=FieldEvidence(page=0, text="R$ 3.900,00"),
            ),
            total_descontos=ExtractedField(
                value=None, currency=None, method=None, evidence=None
            ),
            linhas_consignado=[],
            alerts=[],
        ),
        PaymentExtractionResult(
            competencia="2024-02",  # Mais recente (formato diferente)
            salario_bruto=ExtractedField(
                value=5200.0,
                currency="BRL",
                method="EXTRACTED",
                evidence=FieldEvidence(page=0, text="R$ 5.200,00"),
            ),
            salario_liquido=ExtractedField(
                value=4100.0,
                currency="BRL",
                method="EXTRACTED",
                evidence=FieldEvidence(page=0, text="R$ 4.100,00"),
            ),
            total_descontos=ExtractedField(
                value=None, currency=None, method=None, evidence=None
            ),
            linhas_consignado=[],
            alerts=[],
        ),
    ]

    # Selecionar competência alvo
    competencia, alert = consolidator.select_target_competencia(results)

    print(f"\n📅 Competência selecionada: {competencia}")
    if alert:
        print(f"⚠️  Alerta: {alert.message}")

    # Verificar
    checks = [
        ("Formato normalizado", competencia.count("-") == 1),
        ("Competência mais recente", competencia == "2024-02"),
        ("Sem alertas", alert is None),
    ]

    all_passed = True
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"{status} {check_name}")
        if not check_result:
            all_passed = False

    return all_passed


def test_source_priority():
    """Testa consolidação com prioridade de fontes (RF-009)."""
    from app.services.consolidator import ConsolidatorService, DocumentSource
    from app.services.extractors import (
        ExtractedField,
        FieldEvidence,
        PaymentExtractionResult,
    )

    print("\n" + "=" * 60)
    print("Teste 2: Prioridade de Fontes")
    print("=" * 60)

    consolidator = ConsolidatorService()

    # Criar múltiplos resultados da MESMA competência mas de fontes diferentes
    results = [
        PaymentExtractionResult(
            competencia="2024-01",
            salario_bruto=ExtractedField(
                value=5000.0,  # Valor da PAYROLL (prioridade alta)
                currency="BRL",
                method="EXTRACTED",
                evidence=FieldEvidence(page=0, text="R$ 5.000,00"),
            ),
            salario_liquido=ExtractedField(
                value=4000.0,
                currency="BRL",
                method="EXTRACTED",
                evidence=FieldEvidence(page=0, text="R$ 4.000,00"),
            ),
            total_descontos=ExtractedField(
                value=None, currency=None, method=None, evidence=None
            ),
            linhas_consignado=[],
            alerts=[],
        ),
        PaymentExtractionResult(
            competencia="2024-01",
            salario_bruto=ExtractedField(
                value=5100.0,  # Valor do INSS (prioridade média)
                currency="BRL",
                method="EXTRACTED",
                evidence=FieldEvidence(page=0, text="R$ 5.100,00"),
            ),
            salario_liquido=ExtractedField(
                value=4050.0,
                currency="BRL",
                method="EXTRACTED",
                evidence=FieldEvidence(page=0, text="R$ 4.050,00"),
            ),
            total_descontos=ExtractedField(
                value=None, currency=None, method=None, evidence=None
            ),
            linhas_consignado=[],
            alerts=[],
        ),
    ]

    # Mapear fontes (PAYROLL tem prioridade sobre INSS para bruto)
    doc_sources = {
        "payment_0": DocumentSource.PAYROLL_SALARY_STATEMENT,
        "payment_1": DocumentSource.INSS_HISTORICO_CREDITOS,
    }

    # Consolidar
    consolidated = consolidator.consolidate(
        payment_results=results, loan_results=[], doc_sources=doc_sources
    )

    print(f"\n💰 Salário bruto consolidado: R$ {consolidated.salario_bruto.value_cent/100:.2f}")
    print(f"📄 Fonte: {consolidated.salario_bruto.source.value}")
    print(f"⚠️  Alertas: {len(consolidated.alerts)}")

    # Verificar que PAYROLL foi escolhido (prioridade HIGHEST)
    checks = [
        ("Valor correto (PAYROLL)", consolidated.salario_bruto.value_cent == 500000),
        (
            "Fonte correta",
            consolidated.salario_bruto.source == DocumentSource.PAYROLL_SALARY_STATEMENT,
        ),
    ]

    all_passed = True
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"{status} {check_name}")
        if not check_result:
            all_passed = False

    return all_passed


def test_compute_engine_calculations():
    """Testa cálculos determinísticos do Compute Engine (RF-010)."""
    from app.services.compute_engine import ComputeEngine, ComputeMethod
    from app.services.consolidator import (
        ConsolidatedData,
        ConsolidatedValue,
        DocumentSource,
    )
    from app.services.extractors import ConsignadoLine, FieldEvidence, LoanContractResult, ExtractedField

    print("\n" + "=" * 60)
    print("Teste 3: Compute Engine - Cálculos em Centavos")
    print("=" * 60)

    engine = ComputeEngine()

    # Criar linha de consignado
    linha = ConsignadoLine(
        descricao="Banco ABC",
        rubrica="216",
        valor_cent=25000,  # R$ 250,00
        evidence=FieldEvidence(page=0, text="R$ 250,00"),
    )

    # Criar contrato
    contrato = LoanContractResult(
        lender_name="Banco XYZ",
        contract_id="123",
        parcela_mensal=ExtractedField(
            value=350.0,
            currency="BRL",
            method="EXTRACTED",
            evidence=FieldEvidence(page=0, text="R$ 350,00"),
        ),
        total_parcelas=36,
        parcelas_pagas=12,
        parcelas_restantes=24,
        valor_total=ExtractedField(
            value=10000.0,
            currency="BRL",
            method="EXTRACTED",
            evidence=FieldEvidence(page=0, text="R$ 10.000,00"),
        ),
        taxa_juros="2.5% a.m.",
        alerts=[],
    )

    # Criar dados consolidados
    consolidated = ConsolidatedData(
        competencia_alvo="2024-01",
        renda_competencia=None,
        perfil_dados=None,
        salario_bruto=ConsolidatedValue(
            value_cent=500000,  # R$ 5.000,00
            source=DocumentSource.PAYROLL_SALARY_STATEMENT,
            method="EXTRACTED",
            document_id="doc1",
            confidence=1.0,
        ),
        salario_liquido=ConsolidatedValue(
            value_cent=400000,  # R$ 4.000,00
            source=DocumentSource.PAYROLL_SALARY_STATEMENT,
            method="EXTRACTED",
            document_id="doc1",
            confidence=1.0,
        ),
        total_descontos=None,  # Será calculado
        consignado_mensal=None,  # Será calculado
        divida_total_consignada=None,  # Será calculado
        parcelas_restantes_total=None,  # Será calculado
        linhas_consignado=[linha],
        contratos=[contrato],
        alerts=[],
    )

    # Executar cálculos
    result = engine.compute(consolidated)

    print("\n📊 Resultados dos cálculos:")
    print(f"   Bruto: R$ {result.salario_bruto_cent/100:.2f}")
    print(f"   Líquido: R$ {result.salario_liquido_cent/100:.2f}")
    print(f"   Descontos: R$ {result.total_descontos_cent/100:.2f} (método: {result.descontos_method})")
    print(f"   Dívida Mensal: R$ {result.divida_mensal_cent/100:.2f} (método: {result.divida_mensal_method})")
    print(f"   Dívida Mensal Reduzida: R$ {result.divida_mensal_reduzida_cent/100:.2f} (método: {result.divida_mensal_reduzida_method})")
    print(f"   Consignado Mensal: R$ {result.consignado_mensal_cent/100:.2f} (método: {result.consignado_method})")
    print(f"   Dívida Total: R$ {result.divida_total_consignada_cent/100:.2f} (método: {result.divida_method})")
    print(f"   Dívida Total Reduzida: R$ {result.divida_total_reduzida_cent/100:.2f} (método: {result.divida_total_reduzida_method})")
    print(f"   Parcelas Restantes: {result.parcelas_restantes_total} (método: {result.parcelas_method})")
    print(f"   Alertas: {len(result.alerts)}")

    # Verificar cálculos
    checks = [
        ("Descontos = Bruto - Líquido", result.total_descontos_cent == 100000),  # R$ 1.000,00
        ("Método descontos correto", result.descontos_method == ComputeMethod.DIFFERENCE),
        ("Dívida mensal = 90% descontos", result.divida_mensal_cent == 90000),  # R$ 900,00
        ("Método dívida mensal correto", result.divida_mensal_method == ComputeMethod.PERCENTAGE_90),
        ("Dívida mensal reduzida = 25% dívida mensal", result.divida_mensal_reduzida_cent == 22500),  # R$ 225,00
        ("Método dívida mensal reduzida correto", result.divida_mensal_reduzida_method == ComputeMethod.PERCENTAGE_25),
        ("Consignado = Soma linhas", result.consignado_mensal_cent == 25000),  # R$ 250,00
        ("Método consignado correto", result.consignado_method == ComputeMethod.SUM_LINES),
        ("Dívida = Soma contratos", result.divida_total_consignada_cent == 1000000),  # R$ 10.000,00
        ("Dívida total reduzida = 25% dívida total", result.divida_total_reduzida_cent == 250000),  # R$ 2.500,00
        ("Método dívida total reduzida correto", result.divida_total_reduzida_method == ComputeMethod.PERCENTAGE_25_DIVIDA_TOTAL),
        ("Parcelas restantes corretas", result.parcelas_restantes_total == 24),
        ("Sem alertas de erro", len([a for a in result.alerts if a.severity == "ERROR"]) == 0),
    ]

    all_passed = True
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"{status} {check_name}")
        if not check_result:
            all_passed = False

    return all_passed


def test_conflict_detection():
    """Testa detecção de conflitos entre fontes (RF-009 CA-003)."""
    from app.services.consolidator import ConsolidatorService, DocumentSource
    from app.services.extractors import (
        ExtractedField,
        FieldEvidence,
        PaymentExtractionResult,
    )

    print("\n" + "=" * 60)
    print("Teste 4: Detecção de Conflitos")
    print("=" * 60)

    consolidator = ConsolidatorService(conflict_tolerance_percent=1.0)

    # Criar dois resultados com MESMA prioridade mas valores divergentes
    results = [
        PaymentExtractionResult(
            competencia="2024-01",
            salario_bruto=ExtractedField(
                value=5000.0,
                currency="BRL",
                method="EXTRACTED",
                evidence=FieldEvidence(page=0, text="R$ 5.000,00"),
            ),
            salario_liquido=ExtractedField(
                value=4000.0,
                currency="BRL",
                method="EXTRACTED",
                evidence=FieldEvidence(page=0, text="R$ 4.000,00"),
            ),
            total_descontos=ExtractedField(
                value=None, currency=None, method=None, evidence=None
            ),
            linhas_consignado=[],
            alerts=[],
        ),
        PaymentExtractionResult(
            competencia="2024-01",
            salario_bruto=ExtractedField(
                value=5150.0,  # Divergência de 3% (acima da tolerância de 1%)
                currency="BRL",
                method="EXTRACTED",
                evidence=FieldEvidence(page=0, text="R$ 5.150,00"),
            ),
            salario_liquido=ExtractedField(
                value=4000.0,
                currency="BRL",
                method="EXTRACTED",
                evidence=FieldEvidence(page=0, text="R$ 4.000,00"),
            ),
            total_descontos=ExtractedField(
                value=None, currency=None, method=None, evidence=None
            ),
            linhas_consignado=[],
            alerts=[],
        ),
    ]

    # Ambos com mesma fonte (PAYROLL) = mesma prioridade
    doc_sources = {
        "payment_0": DocumentSource.PAYROLL_SALARY_STATEMENT,
        "payment_1": DocumentSource.PAYROLL_SALARY_STATEMENT,
    }

    # Consolidar
    consolidated = consolidator.consolidate(
        payment_results=results, loan_results=[], doc_sources=doc_sources
    )

    print(f"\n⚠️  Alertas gerados: {len(consolidated.alerts)}")
    for alert in consolidated.alerts:
        print(f"   - {alert.field_name}: {alert.message}")

    # Verificar que alerta de conflito foi gerado
    conflict_alerts = [a for a in consolidated.alerts if "Conflito" in a.message]

    checks = [
        ("Alerta de conflito gerado", len(conflict_alerts) > 0),
        ("Valor consolidado é o primeiro", consolidated.salario_bruto.value_cent == 500000),
    ]

    all_passed = True
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"{status} {check_name}")
        if not check_result:
            all_passed = False

    return all_passed


def main():
    """Executa todos os testes."""
    try:
        # Teste 1: Seleção de competência
        result1 = test_competencia_selection()

        # Teste 2: Prioridade de fontes
        result2 = test_source_priority()

        # Teste 3: Cálculos do Compute Engine
        result3 = test_compute_engine_calculations()

        # Teste 4: Detecção de conflitos
        result4 = test_conflict_detection()

        # Resultado final
        print("\n" + "=" * 60)
        all_passed = result1 and result2 and result3 and result4
        if all_passed:
            print("✅ Todos os testes do Consolidator & Compute passaram!")
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
