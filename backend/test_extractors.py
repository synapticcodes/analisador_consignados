#!/usr/bin/env python3
"""
Teste dos Extractors LLM (Payment e Loan).
"""

import asyncio
import sys


async def test_payment_extractor():
    """Testa Payment Extractor com folha de pagamento."""
    from app.services.extractors import PaymentExtractor
    from app.services.llm_client import MockLLMClient

    print("=" * 60)
    print("Teste 1: Payment Extractor")
    print("=" * 60)

    # Setup
    print("\n1. Inicializando services...")
    llm_client = MockLLMClient()
    extractor = PaymentExtractor(llm_client=llm_client)
    print("   ✅ Services inicializados")

    # Texto de folha de pagamento
    print("\n2. Criando documento de teste...")
    payroll_text = """
FOLHA DE PAGAMENTO
Competência: 01/2024
Funcionário: João Silva Santos
CPF: 123.456.789-00
Matrícula: 12345

PROVENTOS
Salário Base:                   R$ 5.000,00
Adicional Noturno:              R$ 500,00
Total de Proventos:             R$ 5.500,00

DESCONTOS
INSS:                           R$ 605,00
IRRF:                           R$ 350,00
Consignado Banco ABC (216):     R$ 250,00
Consignado Banco XYZ (217):     R$ 180,00
Total de Descontos:             R$ 1.385,00

LÍQUIDO A RECEBER:              R$ 4.115,00
"""
    print(f"   ✅ Documento criado ({len(payroll_text)} chars)")

    # Extrair dados
    print("\n3. Extraindo dados...")
    result = await extractor.extract(text=payroll_text, competencia="2024-01")
    print("   ✅ Extração concluída")

    # Validar resultado
    print("\n4. Validando resultado...")
    print(f"   📅 Competência: {result.competencia}")
    print(f"   💰 Salário Bruto: R$ {result.salario_bruto.value}")
    print(f"   💵 Salário Líquido: R$ {result.salario_liquido.value}")
    print(f"   📉 Total Descontos: R$ {result.total_descontos.value}")
    print(f"   🏦 Linhas Consignado: {len(result.linhas_consignado)}")
    print(f"   ⚠️  Alertas: {len(result.alerts)}")

    # Validar linhas de consignado
    if len(result.linhas_consignado) > 0:
        print("\n5. Validando linhas de consignado...")
        for i, linha in enumerate(result.linhas_consignado, 1):
            print(f"   Linha {i}:")
            print(f"      Descrição: {linha.descricao}")
            print(f"      Rubrica: {linha.rubrica}")
            print(f"      Valor: R$ {linha.valor_cent / 100:.2f}")
            print(f"      Evidence: '{linha.evidence.text[:50]}...'")

    # Checks
    checks = [
        ("Competência extraída", result.competencia == "2024-01"),
        ("Salário bruto extraído", result.salario_bruto.value is not None),
        ("Salário líquido extraído", result.salario_liquido.value is not None),
        ("Linhas consignado extraídas", len(result.linhas_consignado) >= 2),
        ("Evidências presentes", result.salario_bruto.evidence is not None),
        ("Sem alertas", len(result.alerts) == 0),
    ]

    all_passed = True
    print("\n6. Checks finais...")
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"   {status} {check_name}")
        if not check_result:
            all_passed = False

    return all_passed


async def test_loan_extractor():
    """Testa Loan Extractor com contrato de empréstimo."""
    from app.services.extractors import LoanExtractor
    from app.services.llm_client import MockLLMClient

    print("\n" + "=" * 60)
    print("Teste 2: Loan Extractor")
    print("=" * 60)

    # Setup
    print("\n1. Inicializando services...")
    llm_client = MockLLMClient()
    extractor = LoanExtractor(llm_client=llm_client)
    print("   ✅ Services inicializados")

    # Texto de contrato
    print("\n2. Criando documento de teste...")
    contract_text = """
CONTRATO DE EMPRÉSTIMO CONSIGNADO
Nº 123456789

CONTRATANTE: Banco Exemplo S.A.
CONTRATADO: Maria Santos Silva
CPF: 987.654.321-00

CONDIÇÕES DO EMPRÉSTIMO:
Valor Total do Contrato:        R$ 10.000,00
Valor da Parcela:                R$ 350,00
Número de Parcelas:              36
Taxa de Juros Mensal:            2.5%
CET (Custo Efetivo Total):       45.6% a.a.

Data de Início:                  01/01/2024
Data de Término:                 01/12/2026

As parcelas serão descontadas diretamente em folha de pagamento.
"""
    print(f"   ✅ Documento criado ({len(contract_text)} chars)")

    # Extrair dados
    print("\n3. Extraindo dados...")
    result = await extractor.extract(text=contract_text)
    print("   ✅ Extração concluída")

    # Validar resultado
    print("\n4. Validando resultado...")
    print(f"   🏦 Banco: {result.lender_name}")
    print(f"   📄 Contrato: {result.contract_id}")
    print(f"   💰 Parcela Mensal: R$ {result.parcela_mensal.value}")
    print(f"   🔢 Total Parcelas: {result.total_parcelas}")
    print(f"   💵 Valor Total: R$ {result.valor_total.value}")
    print(f"   📊 Taxa Juros: {result.taxa_juros}")
    print(f"   ⚠️  Alertas: {len(result.alerts)}")

    # Checks
    checks = [
        ("Banco extraído", result.lender_name is not None),
        ("Contrato ID extraído", result.contract_id is not None),
        ("Parcela mensal extraída", result.parcela_mensal.value is not None),
        ("Total parcelas extraído", result.total_parcelas is not None),
        ("Valor total extraído", result.valor_total.value is not None),
        ("Taxa juros extraída", result.taxa_juros is not None),
        ("Evidências presentes", result.parcela_mensal.evidence is not None),
        ("Sem alertas", len(result.alerts) == 0),
    ]

    all_passed = True
    print("\n5. Checks finais...")
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"   {status} {check_name}")
        if not check_result:
            all_passed = False

    return all_passed


async def test_integration_router_plus_extractors():
    """Testa integração: Router → Extractor apropriado."""
    from app.services.extractors import LoanExtractor, PaymentExtractor
    from app.services.llm_client import MockLLMClient
    from app.services.router import RouterService

    print("\n" + "=" * 60)
    print("Teste 3: Integração Router + Extractors")
    print("=" * 60)

    # Setup
    print("\n1. Inicializando services...")
    llm_client = MockLLMClient()
    router = RouterService(llm_client=llm_client)
    payment_extractor = PaymentExtractor(llm_client=llm_client)
    loan_extractor = LoanExtractor(llm_client=llm_client)
    print("   ✅ Services inicializados")

    # Documento de folha de pagamento
    print("\n2. Testando fluxo completo com folha...")
    payroll_text = """
FOLHA DE PAGAMENTO
Competência: 01/2024
Funcionário: João Silva
PROVENTOS: R$ 5.500,00
DESCONTOS: R$ 1.385,00
Consignado Banco ABC (216): R$ 250,00
Consignado Banco XYZ (217): R$ 180,00
LÍQUIDO: R$ 4.115,00
"""

    # Router classifica
    router_result = await router.classify_document(
        text=payroll_text, metadata={"filename": "folha.pdf"}
    )
    print(f"   📄 Router classificou como: {router_result.doc_family}")

    # Seleciona extractor apropriado
    if router_result.doc_family == "PAYROLL_SALARY_STATEMENT":
        print("   ✅ Selecionando Payment Extractor...")
        extraction_result = await payment_extractor.extract(
            text=payroll_text, competencia=router_result.competencias_detectadas[0]
        )
        print(f"   💰 Salário Bruto: R$ {extraction_result.salario_bruto.value}")
        payroll_ok = extraction_result.salario_bruto.value is not None
    else:
        payroll_ok = False

    # Documento de contrato
    print("\n3. Testando fluxo completo com contrato...")
    contract_text = """
CONTRATO DE EMPRÉSTIMO CONSIGNADO
Nº 123456789
CONTRATANTE: Banco Exemplo S.A.
CONTRATADO: Maria Santos
Valor Total do Contrato: R$ 10.000,00
Valor da Parcela: R$ 350,00
Número de Parcelas: 36
Taxa de Juros Mensal: 2.5%
"""

    # Router classifica
    router_result2 = await router.classify_document(
        text=contract_text, metadata={"filename": "contrato.pdf"}
    )
    print(f"   📄 Router classificou como: {router_result2.doc_family}")

    # Seleciona extractor apropriado
    if router_result2.doc_family == "LOAN_CONTRACT_GENERIC":
        print("   ✅ Selecionando Loan Extractor...")
        extraction_result2 = await loan_extractor.extract(text=contract_text)
        print(f"   💰 Parcela Mensal: R$ {extraction_result2.parcela_mensal.value}")
        contract_ok = extraction_result2.parcela_mensal.value is not None
    else:
        contract_ok = False

    # Validação final
    print("\n4. Validação final...")
    checks = [
        ("Folha classificada corretamente", payroll_ok),
        ("Contrato classificado corretamente", contract_ok),
    ]

    all_passed = True
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"   {status} {check_name}")
        if not check_result:
            all_passed = False

    return all_passed


async def main():
    """Executa todos os testes."""
    try:
        # Teste 1: Payment Extractor
        result1 = await test_payment_extractor()

        # Teste 2: Loan Extractor
        result2 = await test_loan_extractor()

        # Teste 3: Integração Router + Extractors
        result3 = await test_integration_router_plus_extractors()

        # Resultado final
        print("\n" + "=" * 60)
        all_passed = result1 and result2 and result3
        if all_passed:
            print("✅ Todos os testes dos Extractors passaram!")
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
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
