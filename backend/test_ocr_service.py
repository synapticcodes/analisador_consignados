#!/usr/bin/env python3
"""
Teste do OCR Service (Mock).
"""

import asyncio
import sys


async def test_mock_ocr_service():
    """Testa o Mock OCR Service."""
    from app.services.ocr_service import MockOCRService

    print("=" * 60)
    print("Teste do Mock OCR Service")
    print("=" * 60)

    # Inicializar mock service
    print("\n1. Inicializando Mock OCR Service...")
    service = MockOCRService()
    print("   ✅ Service inicializado")

    # Verificar configuração
    print("\n2. Verificando configuração...")
    is_configured = service.is_configured()
    print(f"   ✅ Configurado: {is_configured}")

    if not is_configured:
        print("   ❌ Mock service deveria estar sempre configurado")
        return False

    # Criar PDF de teste (dummy bytes)
    print("\n3. Criando PDF de teste...")
    dummy_pdf = b"%PDF-1.4 dummy content"
    print(f"   ✅ PDF criado ({len(dummy_pdf)} bytes)")

    # Extrair texto com OCR
    print("\n4. Extraindo texto com OCR...")
    result = await service.extract_text(dummy_pdf)
    print(f"   ✅ Extração concluída em {result.processing_time_ms}ms")

    # Validar resultado
    print("\n5. Validando resultado...")
    print(f"   📝 Texto: '{result.text}'")
    print(f"   📊 Confiança: {result.confidence:.2f}")
    print(f"   📄 Páginas: {result.page_count}")

    if not result.text:
        print("   ❌ Texto extraído está vazio")
        return False

    if result.confidence < 0 or result.confidence > 1:
        print(f"   ❌ Confiança ({result.confidence}) fora do range [0-1]")
        return False

    # Testar extração de tabelas
    print("\n6. Testando extração de tabelas...")
    tables = await service.extract_tables(dummy_pdf)
    print(f"   ✅ Extraídas {len(tables)} tabelas")

    if len(tables) > 0:
        print(f"   📊 Primeira tabela: {tables[0]}")

    print("\n" + "=" * 60)
    print("✅ Todos os testes passaram!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_mock_ocr_service())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
