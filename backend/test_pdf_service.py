#!/usr/bin/env python3
"""
Teste simples do PDF Extraction Service.
Cria um PDF de teste e valida a extração.
"""

import io
import sys


def create_test_pdf() -> bytes:
    """Cria um PDF de teste usando PyMuPDF."""
    import fitz  # PyMuPDF

    # Criar novo documento PDF
    doc = fitz.open()
    page = doc.new_page()

    # Adicionar texto financeiro ao PDF
    text = """
FOLHA DE PAGAMENTO

Funcionário: João Silva
CPF: 123.456.789-00
Competência: 01/2024

Salário Bruto: R$ 5.000,00
Descontos: R$ 1.200,00
Salário Líquido: R$ 3.800,00

Consignado Banco A: R$ 250,00
Consignado Banco B: R$ 180,00
"""

    # Inserir texto na página
    page.insert_text((100, 100), text, fontsize=12)

    # Salvar em buffer
    pdf_bytes = doc.tobytes()
    doc.close()

    return pdf_bytes


def test_pdf_extraction():
    """Testa o PDF Extraction Service."""
    from app.services.pdf_extraction import PDFExtractionService

    print("=" * 60)
    print("Teste do PDF Extraction Service")
    print("=" * 60)

    # Criar PDF de teste
    print("\n1. Criando PDF de teste...")
    pdf_bytes = create_test_pdf()
    print(f"   ✅ PDF criado ({len(pdf_bytes)} bytes)")

    # Inicializar service
    print("\n2. Inicializando PDF Extraction Service...")
    service = PDFExtractionService(ocr_quality_threshold=0.6)
    print("   ✅ Service inicializado")

    # Extrair texto
    print("\n3. Extraindo texto do PDF...")
    result = service.extract_from_bytes(pdf_bytes, filename="teste.pdf")
    print(f"   ✅ Extração concluída em {result.extraction_time_ms}ms")

    # Validar resultado
    print("\n4. Validando resultado...")
    print(f"   📄 Páginas: {result.page_count}")
    print(f"   📊 Tamanho: {result.file_size_bytes} bytes")
    print(f"   ⭐ Qualidade: {result.quality_score:.2f}")
    print(f"   🔍 Usou OCR: {result.used_ocr}")

    # Verificar se texto esperado está presente
    expected_texts = [
        "FOLHA DE PAGAMENTO",
        "João Silva",
        "5.000,00",
        "3.800,00",
        "Consignado",
    ]

    print("\n5. Verificando conteúdo extraído...")
    all_found = True
    for text in expected_texts:
        if text in result.text:
            print(f"   ✅ '{text}' encontrado")
        else:
            print(f"   ❌ '{text}' NÃO encontrado")
            all_found = False

    if not all_found:
        print(f"\n   Texto extraído:\n{result.text}\n")
        return False

    # Testar cálculo de qualidade
    print("\n6. Testando cálculo de qualidade...")

    # Texto de boa qualidade
    good_text = "Este é um texto de boa qualidade com palavras reconhecíveis e números 123."
    good_score = service._calculate_quality_score(good_text)
    print(f"   ✅ Texto bom: score={good_score:.2f}")

    # Texto de má qualidade
    bad_text = "��� ��� ��� ���"
    bad_score = service._calculate_quality_score(bad_text)
    print(f"   ✅ Texto ruim: score={bad_score:.2f}")

    if good_score <= bad_score:
        print(f"   ❌ Score de texto bom ({good_score:.2f}) deveria ser maior que ruim ({bad_score:.2f})")
        return False

    # Testar should_use_ocr
    print("\n7. Testando decisão de OCR...")
    should_ocr_good = service.should_use_ocr(good_score)
    should_ocr_bad = service.should_use_ocr(bad_score)
    print(f"   ✅ Texto bom ({good_score:.2f}): OCR={'SIM' if should_ocr_good else 'NÃO'}")
    print(f"   ✅ Texto ruim ({bad_score:.2f}): OCR={'SIM' if should_ocr_bad else 'NÃO'}")

    # Testar extração com coordenadas
    print("\n8. Testando extração com coordenadas...")
    blocks = service.extract_with_coordinates(pdf_bytes)
    print(f"   ✅ Extraídos {len(blocks)} blocos de texto com coordenadas")

    if len(blocks) > 0:
        print(f"   📍 Primeiro bloco: '{blocks[0]['text'][:30]}...'")
        print(f"      Página: {blocks[0]['page']}")
        print(f"      BBox: {blocks[0]['bbox']}")

    print("\n" + "=" * 60)
    print("✅ Todos os testes passaram!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_pdf_extraction()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
