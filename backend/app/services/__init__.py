"""
Services package - Business logic services.
"""

from app.services.compute_engine import ComputeEngine, ComputeMethod, ComputeResult
from app.services.consolidator import (
    ConsolidatedAlert,
    ConsolidatedData,
    ConsolidatedValue,
    ConsolidatorService,
    DocumentSource,
    SourcePriority,
)
from app.services.evidence_gate import (
    BrazilianCurrencyParser,
    EvidenceGate,
    GateResult,
    GateStatus,
    ValidationAlert,
)
from app.services.extractors import (
    ConsignadoLine,
    ExtractedField,
    FieldEvidence,
    LoanContractResult,
    LoanExtractor,
    PaymentExtractor,
    PaymentExtractionResult,
)
from app.services.llm_client import LLMClient, MockLLMClient
from app.services.ocr_service import MockOCRService, OCRResult, OCRService
from app.services.pdf_extraction import PDFExtractionResult, PDFExtractionService
from app.services.router import (
    DocumentCapability,
    DocumentFamily,
    RouterEvidence,
    RouterResult,
    RouterService,
)
from app.services.savings_simulator import (
    SavingsContractSimulation,
    SavingsSimulationResult,
    SavingsSimulator,
)

__all__ = [
    # PDF Extraction
    "PDFExtractionService",
    "PDFExtractionResult",
    # OCR
    "OCRService",
    "MockOCRService",
    "OCRResult",
    # LLM Client
    "LLMClient",
    "MockLLMClient",
    # Router
    "RouterService",
    "RouterResult",
    "RouterEvidence",
    "DocumentFamily",
    "DocumentCapability",
    # Extractors
    "PaymentExtractor",
    "PaymentExtractionResult",
    "LoanExtractor",
    "LoanContractResult",
    "ExtractedField",
    "FieldEvidence",
    "ConsignadoLine",
    # Evidence Gate
    "EvidenceGate",
    "GateResult",
    "GateStatus",
    "ValidationAlert",
    "BrazilianCurrencyParser",
    # Consolidator
    "ConsolidatorService",
    "ConsolidatedData",
    "ConsolidatedValue",
    "ConsolidatedAlert",
    "DocumentSource",
    "SourcePriority",
    # Compute Engine
    "ComputeEngine",
    "ComputeResult",
    "ComputeMethod",
    # Savings Simulator
    "SavingsSimulator",
    "SavingsSimulationResult",
    "SavingsContractSimulation",
]
