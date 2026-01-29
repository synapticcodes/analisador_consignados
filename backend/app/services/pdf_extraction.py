"""
PDF Extraction Service
~~~~~~~~~~~~~~~~~~~~~~

Serviço de extração de texto de PDFs usando PyMuPDF (fitz).
Calcula score de qualidade e aciona OCR quando necessário.
"""

import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import fitz  # PyMuPDF


@dataclass
class PDFExtractionResult:
    """Resultado da extração de PDF."""

    text: str
    page_count: int
    file_size_bytes: int
    quality_score: float
    used_ocr: bool
    extraction_time_ms: int
    metadata: dict


class PDFExtractionService:
    """Serviço de extração de texto de PDFs."""

    def __init__(self, ocr_quality_threshold: float = 0.6):
        """
        Inicializa o serviço de extração de PDFs.

        Args:
            ocr_quality_threshold: Score mínimo para não acionar OCR (0-1)
        """
        self.ocr_quality_threshold = ocr_quality_threshold

    def extract_from_bytes(
        self, pdf_bytes: bytes, filename: str = "document.pdf"
    ) -> PDFExtractionResult:
        """
        Extrai texto de PDF a partir de bytes.

        Args:
            pdf_bytes: Conteúdo do PDF em bytes
            filename: Nome do arquivo (para metadados)

        Returns:
            PDFExtractionResult com texto extraído e metadados

        Raises:
            ValueError: Se o PDF estiver corrompido ou inválido
        """
        import time

        start_time = time.time()

        try:
            # Abrir PDF a partir de bytes
            pdf_stream = BytesIO(pdf_bytes)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")

            # Extrair texto de todas as páginas
            full_text = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                full_text.append(text)

            combined_text = "\n\n".join(full_text)

            # Calcular score de qualidade
            quality_score = self._calculate_quality_score(combined_text)

            # Extrair metadados
            metadata = {
                "filename": filename,
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
            }

            doc.close()

            # Calcular tempo de extração
            extraction_time_ms = int((time.time() - start_time) * 1000)

            return PDFExtractionResult(
                text=combined_text,
                page_count=len(full_text),
                file_size_bytes=len(pdf_bytes),
                quality_score=quality_score,
                used_ocr=False,
                extraction_time_ms=extraction_time_ms,
                metadata=metadata,
            )

        except Exception as e:
            raise ValueError(f"Erro ao extrair texto do PDF: {str(e)}") from e

    def extract_from_file(self, file_path: str | Path) -> PDFExtractionResult:
        """
        Extrai texto de PDF a partir de arquivo.

        Args:
            file_path: Caminho para o arquivo PDF

        Returns:
            PDFExtractionResult com texto extraído e metadados
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        with open(file_path, "rb") as f:
            pdf_bytes = f.read()

        return self.extract_from_bytes(pdf_bytes, filename=file_path.name)

    def _calculate_quality_score(self, text: str) -> float:
        """
        Calcula score de qualidade do texto extraído (0-1).

        Score baseado em:
        - Densidade de caracteres válidos
        - Presença de palavras reconhecíveis
        - Ausência de caracteres de substituição (�, �, etc.)

        Args:
            text: Texto extraído

        Returns:
            Score de qualidade entre 0 e 1
        """
        if not text or len(text.strip()) == 0:
            return 0.0

        # Remover espaços em branco extras
        text_clean = " ".join(text.split())

        # 1. Densidade de caracteres alfanuméricos
        total_chars = len(text_clean)
        if total_chars == 0:
            return 0.0

        alnum_chars = sum(1 for c in text_clean if c.isalnum())
        alnum_density = alnum_chars / total_chars

        # 2. Presença de caracteres de substituição (indica OCR ruim)
        replacement_chars = text_clean.count("�") + text_clean.count("□")
        replacement_penalty = min(replacement_chars / total_chars, 0.5)

        # 3. Densidade de palavras reconhecíveis (3+ caracteres)
        words = text_clean.split()
        recognizable_words = sum(1 for w in words if len(w) >= 3 and w.isalpha())
        word_density = recognizable_words / max(len(words), 1)

        # 4. Presença de números (importante para documentos financeiros)
        has_numbers = any(c.isdigit() for c in text_clean)
        number_bonus = 0.1 if has_numbers else 0.0

        # Score final (média ponderada)
        score = (
            alnum_density * 0.3
            + word_density * 0.4
            + (1 - replacement_penalty) * 0.3
            + number_bonus
        )

        return min(score, 1.0)

    def should_use_ocr(self, quality_score: float) -> bool:
        """
        Determina se deve acionar OCR baseado no score de qualidade.

        Args:
            quality_score: Score de qualidade do texto (0-1)

        Returns:
            True se deve usar OCR, False caso contrário
        """
        return quality_score < self.ocr_quality_threshold

    def extract_tables(self, pdf_bytes: bytes) -> list[dict]:
        """
        Extrai tabelas estruturadas do PDF.

        Args:
            pdf_bytes: Conteúdo do PDF em bytes

        Returns:
            Lista de dicionários representando tabelas encontradas

        Note:
            Implementação básica. Para tabelas complexas, usar pdfplumber.
        """
        # TODO: Implementar extração de tabelas com pdfplumber
        # Por enquanto retorna lista vazia
        return []

    def extract_with_coordinates(self, pdf_bytes: bytes) -> list[dict]:
        """
        Extrai texto com coordenadas de posição (bounding boxes).

        Útil para localizar valores específicos no documento.

        Args:
            pdf_bytes: Conteúdo do PDF em bytes

        Returns:
            Lista de dicionários com texto e coordenadas
        """
        try:
            pdf_stream = BytesIO(pdf_bytes)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")

            all_blocks = []

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Extrair blocos de texto com coordenadas
                blocks = page.get_text("dict")["blocks"]

                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                all_blocks.append(
                                    {
                                        "text": span["text"],
                                        "page": page_num,
                                        "bbox": span["bbox"],  # (x0, y0, x1, y1)
                                        "font": span["font"],
                                        "size": span["size"],
                                    }
                                )

            doc.close()
            return all_blocks

        except Exception as e:
            raise ValueError(f"Erro ao extrair coordenadas: {str(e)}") from e
