"""
OCR Service
~~~~~~~~~~~

Serviço de OCR usando AWS Textract como fallback.
Acionado quando qualidade da extração nativa é baixa.
"""

import asyncio
from dataclasses import dataclass
from typing import Any

try:
    import aioboto3
    from botocore.exceptions import BotoCoreError, ClientError

    AIOBOTO3_AVAILABLE = True
except ImportError:
    AIOBOTO3_AVAILABLE = False


@dataclass
class OCRResult:
    """Resultado da extração via OCR."""

    text: str
    confidence: float
    page_count: int
    processing_time_ms: int
    raw_response: dict | None = None


class OCRService:
    """Serviço de OCR usando AWS Textract."""

    def __init__(
        self,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_region: str = "us-east-1",
    ):
        """
        Inicializa o serviço de OCR.

        Args:
            aws_access_key_id: AWS Access Key ID
            aws_secret_access_key: AWS Secret Access Key
            aws_region: AWS Region

        Raises:
            ImportError: Se aioboto3 não estiver instalado
        """
        if not AIOBOTO3_AVAILABLE:
            raise ImportError(
                "aioboto3 não está instalado. "
                "Instale com: pip install aioboto3"
            )

        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region
        self._session = None

    def is_configured(self) -> bool:
        """
        Verifica se o serviço está configurado com credenciais AWS.

        Returns:
            True se configurado, False caso contrário
        """
        return bool(self.aws_access_key_id and self.aws_secret_access_key)

    async def extract_text(self, pdf_bytes: bytes) -> OCRResult:
        """
        Extrai texto de PDF usando AWS Textract.

        Args:
            pdf_bytes: Conteúdo do PDF em bytes

        Returns:
            OCRResult com texto extraído

        Raises:
            ValueError: Se credenciais não estiverem configuradas
            RuntimeError: Se ocorrer erro no Textract
        """
        import time

        if not self.is_configured():
            raise ValueError(
                "OCR Service não configurado. "
                "Forneça AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY"
            )

        start_time = time.time()

        try:
            # Criar sessão boto3 async
            session = aioboto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region,
            )

            async with session.client("textract") as textract:
                # Detectar texto no documento
                response = await textract.detect_document_text(
                    Document={"Bytes": pdf_bytes}
                )

                # Extrair texto dos blocos
                text_blocks = []
                total_confidence = 0.0
                confidence_count = 0

                for block in response.get("Blocks", []):
                    if block["BlockType"] == "LINE":
                        text_blocks.append(block.get("Text", ""))

                        # Calcular confiança média
                        if "Confidence" in block:
                            total_confidence += block["Confidence"]
                            confidence_count += 1

                full_text = "\n".join(text_blocks)
                avg_confidence = (
                    total_confidence / confidence_count if confidence_count > 0 else 0.0
                )

                processing_time_ms = int((time.time() - start_time) * 1000)

                return OCRResult(
                    text=full_text,
                    confidence=avg_confidence / 100.0,  # Normalizar para 0-1
                    page_count=response.get("DocumentMetadata", {}).get("Pages", 1),
                    processing_time_ms=processing_time_ms,
                    raw_response=response,
                )

        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Erro ao processar OCR com Textract: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Erro inesperado no OCR: {str(e)}") from e

    async def extract_tables(self, pdf_bytes: bytes) -> list[dict]:
        """
        Extrai tabelas estruturadas usando AWS Textract.

        Args:
            pdf_bytes: Conteúdo do PDF em bytes

        Returns:
            Lista de dicionários representando tabelas

        Raises:
            ValueError: Se credenciais não estiverem configuradas
            RuntimeError: Se ocorrer erro no Textract
        """
        if not self.is_configured():
            raise ValueError("OCR Service não configurado")

        try:
            session = aioboto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region,
            )

            async with session.client("textract") as textract:
                # Analisar documento com feature de tabelas
                response = await textract.analyze_document(
                    Document={"Bytes": pdf_bytes}, FeatureTypes=["TABLES"]
                )

                # Processar tabelas
                tables = self._parse_tables(response)
                return tables

        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(
                f"Erro ao extrair tabelas com Textract: {str(e)}"
            ) from e

    def _parse_tables(self, response: dict[str, Any]) -> list[dict]:
        """
        Parse de tabelas da resposta do Textract.

        Args:
            response: Resposta do Textract

        Returns:
            Lista de tabelas estruturadas
        """
        blocks = response.get("Blocks", [])
        tables = []

        # Criar mapa de blocos por ID
        block_map = {block["Id"]: block for block in blocks}

        # Encontrar blocos do tipo TABLE
        for block in blocks:
            if block["BlockType"] == "TABLE":
                table = self._extract_table_data(block, block_map)
                tables.append(table)

        return tables

    def _extract_table_data(
        self, table_block: dict[str, Any], block_map: dict[str, Any]
    ) -> dict:
        """
        Extrai dados de uma tabela específica.

        Args:
            table_block: Bloco da tabela
            block_map: Mapa de todos os blocos

        Returns:
            Dicionário com dados da tabela
        """
        rows: dict[int, dict] = {}

        # Processar células
        if "Relationships" in table_block:
            for relationship in table_block["Relationships"]:
                if relationship["Type"] == "CHILD":
                    for cell_id in relationship["Ids"]:
                        cell = block_map.get(cell_id)
                        if cell and cell["BlockType"] == "CELL":
                            row_index = cell["RowIndex"]
                            col_index = cell["ColumnIndex"]

                            if row_index not in rows:
                                rows[row_index] = {}

                            # Extrair texto da célula
                            cell_text = self._get_cell_text(cell, block_map)
                            rows[row_index][col_index] = cell_text

        # Converter para lista de listas
        table_data = []
        for row_index in sorted(rows.keys()):
            row_data = []
            for col_index in sorted(rows[row_index].keys()):
                row_data.append(rows[row_index][col_index])
            table_data.append(row_data)

        return {"rows": table_data, "row_count": len(table_data)}

    def _get_cell_text(
        self, cell: dict[str, Any], block_map: dict[str, Any]
    ) -> str:
        """
        Extrai texto de uma célula.

        Args:
            cell: Bloco da célula
            block_map: Mapa de blocos

        Returns:
            Texto da célula
        """
        text = ""
        if "Relationships" in cell:
            for relationship in cell["Relationships"]:
                if relationship["Type"] == "CHILD":
                    for word_id in relationship["Ids"]:
                        word = block_map.get(word_id)
                        if word and word["BlockType"] == "WORD":
                            text += word.get("Text", "") + " "
        return text.strip()


class MockOCRService(OCRService):
    """
    Mock do OCR Service para testes e desenvolvimento.
    Retorna texto placeholder ao invés de chamar AWS Textract.
    """

    def __init__(self):
        """Inicializa mock OCR service."""
        # Não chama super().__init__ para evitar necessidade de credenciais
        self.aws_access_key_id = "mock"
        self.aws_secret_access_key = "mock"
        self.aws_region = "us-east-1"

    def is_configured(self) -> bool:
        """Mock sempre está configurado."""
        return True

    async def extract_text(self, pdf_bytes: bytes) -> OCRResult:
        """
        Mock de extração que retorna texto placeholder.

        Args:
            pdf_bytes: Conteúdo do PDF

        Returns:
            OCRResult com texto mock
        """
        import time

        await asyncio.sleep(0.1)  # Simular processamento

        return OCRResult(
            text="[MOCK OCR] Texto extraído via OCR simulado",
            confidence=0.95,
            page_count=1,
            processing_time_ms=100,
            raw_response=None,
        )

    async def extract_tables(self, pdf_bytes: bytes) -> list[dict]:
        """Mock de extração de tabelas."""
        await asyncio.sleep(0.1)
        return [{"rows": [["Header 1", "Header 2"], ["Data 1", "Data 2"]]}]
