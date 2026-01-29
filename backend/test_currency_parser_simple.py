#!/usr/bin/env python3
"""
Teste standalone do Brazilian Currency Parser.
"""

import re


class BrazilianCurrencyParser:
    """Parser de valores monetários brasileiros."""

    # Regex para capturar valores BR
    # Ordem das alternativas é importante:
    # 1. Números com decimais (prioridade para capturar ,XX)
    # 2. Formato brasileiro com separadores de milhares
    # 3. Números inteiros simples
    CURRENCY_PATTERN = re.compile(
        r"(?:R\$\s*)?"  # R$ opcional com espaço opcional
        r"(\d+,\d{2}|\d{1,3}(?:\.\d{3})+(?:,\d{2})?|\d+)"  # Valor: decimal OU BR-format OU inteiro
    )

    @classmethod
    def parse(cls, text: str) -> float | None:
        """Extrai e normaliza valor monetário de texto."""
        if not text:
            return None

        # Procurar padrão de moeda
        match = cls.CURRENCY_PATTERN.search(text)
        if not match:
            return None

        value_str = match.group(1)

        # Normalizar para formato americano
        value_str = value_str.replace(".", "")  # Remove pontos
        value_str = value_str.replace(",", ".")  # Substitui vírgula por ponto

        try:
            return float(value_str)
        except ValueError:
            return None


def test_currency_parser():
    """Testa o parser de moeda brasileira."""
    print("=" * 60)
    print("Teste: Brazilian Currency Parser")
    print("=" * 60)

    test_cases = [
        ("R$ 1.334,36", 1334.36),
        ("1.334,36", 1334.36),
        ("1334,36", 1334.36),
        ("R$ 250,00", 250.00),
        ("250,00", 250.00),
        ("R$ 1.334", 1334.00),
        ("1.334", 1334.00),
        ("1334", 1334.00),
        ("5500", 5500.00),
    ]

    parser = BrazilianCurrencyParser()
    passed = 0
    failed = 0

    print("\nTestando parsing de valores:")
    for i, (text, expected) in enumerate(test_cases, 1):
        result = parser.parse(text)
        status = "✅" if result == expected else "❌"

        if result == expected:
            passed += 1
            print(f"{i}. {status} '{text}' → {result}")
        else:
            failed += 1
            print(f"{i}. {status} '{text}' Esperado: {expected} Obtido: {result}")

    print(f"\nResultado: {passed}/{len(test_cases)} testes passaram")

    # Debug: testar "1334,36" especificamente
    print("\n" + "=" * 60)
    print("DEBUG: Testando '1334,36' passo a passo")
    print("=" * 60)

    text = "1334,36"
    print(f"Texto de entrada: '{text}'")

    # Testar o regex
    pattern = re.compile(
        r"(?:R\$\s*)?"
        r"(\d+,\d{2}|\d{1,3}(?:\.\d{3})+(?:,\d{2})?|\d+)"
    )

    match = pattern.search(text)
    if match:
        print(f"Match encontrado: '{match.group(0)}'")
        print(f"Grupo 1 (valor): '{match.group(1)}'")
        print(f"Posição: {match.start()} - {match.end()}")

        # Processar valor
        value_str = match.group(1)
        print(f"Após captura: '{value_str}'")

        value_str = value_str.replace(".", "")
        print(f"Após remover '.': '{value_str}'")

        value_str = value_str.replace(",", ".")
        print(f"Após trocar ',' por '.': '{value_str}'")

        result = float(value_str)
        print(f"Valor final: {result}")
    else:
        print("Nenhum match encontrado!")

    return failed == 0


if __name__ == "__main__":
    success = test_currency_parser()
    exit(0 if success else 1)
