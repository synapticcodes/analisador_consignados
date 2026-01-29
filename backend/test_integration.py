#!/usr/bin/env python3
"""
Teste de integração: PDF Extraction + OCR Fallback.
"""

import asyncio
import sys


async def test_pdf_with_ocr_fallback():
    """Testa integração entre PDF extraction e OCR fallback."""
    from app.services.ocr_service import MockOCRService
    from app.services.pdf_extraction import PDFExtractionService
    import fitz

    print("=" * 60)
    print("Teste de Integração: PDF + OCR Fallback")
    print("=" * 60)

    # Criar PDF com texto de baixa qualidade (simula scan ruim)
    print("\n1. Criando PDF com texto de baixa qualidade...")
    doc = fitz.open()
    page = doc.new_page()

    # Texto com muitos caracteres de substituição (simula OCR ruim)
    bad_text = "��� ��� FOL�A �� PAGAM�NTO ��� ���"
    page.insert_text((100, 100), bad_text, fontsize=12)

    pdf_bytes = doc.tobytes()
    doc.close()
    print(f"   ✅ PDF criado ({len(pdf_bytes)} bytes)")

    # Inicializar services
    print("\n2. Inicializando services...")
    pdf_service = PDFExtractionService(ocr_quality_threshold=0.6)
    ocr_service = MockOCRService()
    print("   ✅ Services inicializados")

    # Primeira tentativa: extração nativa
    print("\n3. Tentativa 1: Extração nativa do PDF...")
    result = pdf_service.extract_from_bytes(pdf_bytes, filename="bad_scan.pdf")
    print(f"   📊 Qualidade: {result.quality_score:.2f}")
    print(f"   📝 Texto extraído: '{result.text[:50]}...'")

    # Verificar se precisa de OCR
    print("\n4. Verificando necessidade de OCR...")
    needs_ocr = pdf_service.should_use_ocr(result.quality_score)
    print(f"   🔍 Precisa OCR: {needs_ocr}")

    if needs_ocr:
        print("\n5. Usando OCR como fallback...")
        ocr_result = await ocr_service.extract_text(pdf_bytes)
        print(f"   ✅ OCR concluído em {ocr_result.processing_time_ms}ms")
        print(f"   📝 Texto OCR: '{ocr_result.text}'")
        print(f"   📊 Confiança: {ocr_result.confidence:.2f}")

        # Usar texto do OCR se confiança for boa
        if ocr_result.confidence > 0.8:
            final_text = ocr_result.text
            print("   ✅ Usando texto do OCR (alta confiança)")
        else:
            final_text = result.text
            print("   ⚠️  Mantendo texto original (baixa confiança no OCR)")
    else:
        final_text = result.text
        print("\n5. OCR não necessário, usando extração nativa")

    # Criar PDF com texto de boa qualidade
    print("\n6. Criando PDF com texto de boa qualidade...")
    doc = fitz.open()
    page = doc.new_page()

    good_text = """
FOLHA DE PAGAMENTO
Funcionário: Maria Santos
Salário: R$ 4.500,00
"""
    page.insert_text((100, 100), good_text, fontsize=12)

    good_pdf_bytes = doc.tobytes()
    doc.close()
    print(f"   ✅ PDF criado ({len(good_pdf_bytes)} bytes)")

    # Extrair texto de boa qualidade
    print("\n7. Extraindo texto de boa qualidade...")
    good_result = pdf_service.extract_from_bytes(good_pdf_bytes, filename="good_scan.pdf")
    print(f"   📊 Qualidade: {good_result.quality_score:.2f}")

    needs_ocr_good = pdf_service.should_use_ocr(good_result.quality_score)
    print(f"   🔍 Precisa OCR: {needs_ocr_good}")

    if not needs_ocr_good:
        print("   ✅ OCR não necessário (qualidade boa)")
    else:
        print("   ⚠️  OCR acionado quando não deveria")

    # Validação final
    print("\n8. Validação final...")
    checks = [
        ("PDF ruim detectado", needs_ocr),
        ("PDF bom não aciona OCR", not needs_ocr_good),
        ("Score ruim < Score bom", result.quality_score < good_result.quality_score),
    ]

    all_passed = True
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"   {status} {check_name}")
        if not check_result:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ Todos os testes de integração passaram!")
    else:
        print("❌ Alguns testes falharam")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(test_pdf_with_ocr_fallback())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
