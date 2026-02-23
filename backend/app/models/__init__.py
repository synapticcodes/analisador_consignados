"""
Models package - SQLAlchemy models for database tables.

All models are imported here for convenience and to ensure
proper initialization order for relationships.
"""

from app.core.database import Base
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.document_extraction import DocumentExtraction, GateStatus
from app.models.final_result import FinalResult
from app.models.historical_contract import HistoricalContract
from app.models.inss_margin import INSSMargin
from app.models.loan_contract import ContractStatus, LoanContract
from app.models.offer import Offer, OfferKind, PaymentMethod
from app.models.payroll_month import PayrollMonth
from app.models.product import Product
from app.models.uploaded_file import UploadedFile
from app.models.user import User

__all__ = [
    # Base
    "Base",
    # Models
    "User",
    "AnalysisJob",
    "UploadedFile",
    "DocumentExtraction",
    "LoanContract",
    "INSSMargin",
    "HistoricalContract",
    "PayrollMonth",
    "FinalResult",
    "Product",
    "Offer",
    # Enums
    "JobStatus",
    "GateStatus",
    "ContractStatus",
    "OfferKind",
    "PaymentMethod",
]
