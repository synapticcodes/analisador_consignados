#!/usr/bin/env python3
"""
Teste do Router LLM Service.
"""

import asyncio
import sys


async def test_router_with_payroll():
    """Testa Router com documento de folha de pagamento."""
    from app.services.llm_client import MockLLMClient
    from app.services.router import RouterService

    print("=" * 60)
    print("Teste 1: Router com Folha de Pagamento")
    print("=" * 60)

    # Criar mock LLM client
    print("\n1. Inicializando Mock LLM Client...")
    llm_client = MockLLMClient()
    print("   ✅ Client inicializado")

    # Criar Router service
    print("\n2. Inicializando Router Service...")
    router = RouterService(llm_client=llm_client)
    print("   ✅ Router inicializado")

    # Texto de folha de pagamento
    print("\n3. Criando documento de teste (Folha de Pagamento)...")
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

    # Classificar documento
    print("\n4. Classificando documento...")
    result = await router.classify_document(
        text=payroll_text,
        metadata={
            "filename": "folha_pagamento_01_2024.pdf",
            "page_count": 1,
            "file_size_bytes": len(payroll_text),
        },
    )
    print(f"   ✅ Classificação concluída")

    # Validar resultado
    print("\n5. Validando resultado...")
    print(f"   📄 Família: {result.doc_family}")
    print(f"   📊 Confiança: {result.confidence:.2f}")
    print(f"   🎯 Capabilities: {result.capabilities}")
    print(f"   📅 Competências: {result.competencias_detectadas}")
    print(f"   📝 Evidências: {len(result.evidence)}")

    # Checks
    checks = [
        ("Família correta", result.doc_family == "PAYROLL_SALARY_STATEMENT"),
        ("Confiança >= 0.8", result.confidence >= 0.8),
        ("Tem capabilities", len(result.capabilities) > 0),
        ("Detectou competência", len(result.competencias_detectadas) > 0),
        ("Tem evidências", len(result.evidence) >= 1),
    ]

    all_passed = True
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"   {status} {check_name}")
        if not check_result:
            all_passed = False

    # Converter para dict (para persistir em DB)
    print("\n6. Testando serialização...")
    result_dict = router.to_dict(result)
    print(f"   ✅ Dict criado: {list(result_dict.keys())}")

    return all_passed


async def test_router_with_loan_contract():
    """Testa Router com contrato de empréstimo."""
    from app.services.llm_client import MockLLMClient
    from app.services.router import RouterService

    print("\n" + "=" * 60)
    print("Teste 2: Router com Contrato de Empréstimo")
    print("=" * 60)

    # Setup
    print("\n1. Inicializando services...")
    llm_client = MockLLMClient()
    router = RouterService(llm_client=llm_client)
    print("   ✅ Services inicializados")

    # Texto de contrato
    print("\n2. Criando documento de teste (Contrato)...")
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

    # Classificar
    print("\n3. Classificando documento...")
    result = await router.classify_document(
        text=contract_text,
        metadata={"filename": "contrato_emprestimo.pdf", "page_count": 2},
    )
    print("   ✅ Classificação concluída")

    # Validar
    print("\n4. Validando resultado...")
    print(f"   📄 Família: {result.doc_family}")
    print(f"   📊 Confiança: {result.confidence:.2f}")
    print(f"   🎯 Capabilities: {result.capabilities}")

    checks = [
        ("Família correta", "LOAN" in result.doc_family or "CONTRACT" in result.doc_family),
        ("Confiança >= 0.7", result.confidence >= 0.7),
        ("Capability LOAN", any("LOAN" in cap for cap in result.capabilities)),
    ]

    all_passed = True
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"   {status} {check_name}")
        if not check_result:
            all_passed = False

    return all_passed


async def test_router_with_unknown():
    """Testa Router com documento irrelevante."""
    from app.services.llm_client import MockLLMClient
    from app.services.router import RouterService

    print("\n" + "=" * 60)
    print("Teste 3: Router com Documento Irrelevante")
    print("=" * 60)

    # Setup
    print("\n1. Inicializando services...")
    llm_client = MockLLMClient()
    router = RouterService(llm_client=llm_client)
    print("   ✅ Services inicializados")

    # Texto irrelevante
    print("\n2. Criando documento de teste (Irrelevante)...")
    unknown_text = """
Manual do Usuário
Produto: Cafeteira XYZ

Instruções de uso:
1. Conecte o aparelho na tomada
2. Adicione água no reservatório
3. Coloque o café no filtro
4. Pressione o botão liga/desliga

Especificações técnicas:
- Voltagem: 110V ou 220V
- Potência: 800W
- Capacidade: 1.5L
"""
    print(f"   ✅ Documento criado ({len(unknown_text)} chars)")

    # Classificar
    print("\n3. Classificando documento...")
    result = await router.classify_document(
        text=unknown_text, metadata={"filename": "manual_cafeteira.pdf"}
    )
    print("   ✅ Classificação concluída")

    # Validar
    print("\n4. Validando resultado...")
    print(f"   📄 Família: {result.doc_family}")
    print(f"   📊 Confiança: {result.confidence:.2f}")
    print(f"   🎯 Capabilities: {result.capabilities}")

    checks = [
        ("Família OTHER_UNKNOWN", result.doc_family == "OTHER_UNKNOWN"),
        ("Baixa confiança", result.confidence < 0.5),
        ("Sem capabilities", len(result.capabilities) == 0),
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
        # Teste 1: Folha de pagamento
        result1 = await test_router_with_payroll()

        # Teste 2: Contrato
        result2 = await test_router_with_loan_contract()

        # Teste 3: Documento irrelevante
        result3 = await test_router_with_unknown()

        # Resultado final
        print("\n" + "=" * 60)
        all_passed = result1 and result2 and result3
        if all_passed:
            print("✅ Todos os testes do Router passaram!")
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
