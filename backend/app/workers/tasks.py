"""
Celery Tasks
~~~~~~~~~~~~

Tasks assíncronas para processamento de jobs de análise.
"""

import asyncio
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
from uuid import UUID

from celery import Task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import create_engine_and_session
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.final_result import FinalResult
from app.models.historical_contract import HistoricalContract
from app.models.inss_margin import INSSMargin
from app.models.loan_contract import ContractStatus, LoanContract
from app.models.offer import Offer
from app.models.payroll_month import PayrollMonth
from app.models.product import Product
from app.models.document_extraction import DocumentExtraction
from app.models.uploaded_file import UploadedFile
from app.services.compute_engine import ComputeEngine
from app.services.consolidator import ConsolidatorService, DocumentSource
from app.services.evidence_gate import EvidenceGate
from app.services.extractors import (
    LoanContractResult,
    LoanExtractor,
    PaymentExtractor,
    PaymentExtractionResult,
)
from app.services.llm_client import LLMClient, MockLLMClient
from app.services.ocr_service import OCRService
from app.services.offers import generate_offers
from app.services.offer_salary_base import (
    MIN_OFFER_QUALIFICATION_CENT,
    is_offer_qualified,
    resolve_offer_salary_cent,
)
from app.services.pdf_extraction import PDFExtractionService
from app.services.router import RouterService
from app.workers.celery_app import celery_app


class JobProcessingError(Exception):
    """Erro durante processamento de job."""

    pass


@celery_app.task(bind=True, name="process_job")
def process_job_task(self: Task, job_id: str) -> dict:
    """
    Task principal que orquestra todo o pipeline de processamento.

    Args:
        job_id: UUID do job a ser processado

    Returns:
        Dicionário com resultado do processamento

    Esta task executa:
    1. PDF Extraction (extrai texto)
    2. Router (classifica documentos)
    3. Extractors (extrai dados estruturados)
    4. Evidence Gate (valida evidências)
    5. Consolidator (resolve conflitos)
    6. Compute Engine (calcula outputs finais)
    7. Persistência do resultado
    """
    # Converter job_id para UUID
    try:
        job_uuid = UUID(job_id)
    except ValueError as e:
        raise JobProcessingError(f"Invalid job_id: {job_id}") from e

    # Executar pipeline assíncrono com novo event loop
    result = asyncio.run(_process_job_async(job_uuid, self))

    return result


async def _process_job_async(job_id: UUID, task: Task) -> dict:
    """
    Processamento assíncrono do job.

    Args:
        job_id: UUID do job
        task: Instância da task Celery (para atualizar progresso)

    Returns:
        Dicionário com resultado
    """
    start_time = datetime.now(timezone.utc)

    engine, session_maker = create_engine_and_session()
    try:
        async with session_maker() as db:
            # 1. Buscar job
            result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
            job = result.scalar_one_or_none()

            if not job:
                raise JobProcessingError(f"Job not found: {job_id}")

            # Atualizar status para RUNNING
            job.status = JobStatus.RUNNING.value
            await db.commit()

            # 2. Buscar arquivos uploaded
            result = await db.execute(
                select(UploadedFile).where(UploadedFile.job_id == job_id)
            )
            files = result.scalars().all()

            if not files:
                raise JobProcessingError(f"No files found for job: {job_id}")

            # 3. Inicializar services
            # NOTA: Usa Mock apenas em ambiente de teste ou sem API key válida
            use_mock = (
                settings.environment == "test"
                or settings.openai_api_key == "test-openai-key"
            )
            llm_client = MockLLMClient() if use_mock else LLMClient()

            pdf_service = PDFExtractionService(
                ocr_quality_threshold=settings.ocr_quality_threshold
            )
            ocr_service = None
            try:
                ocr_service = OCRService(
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    aws_region=settings.aws_region,
                )
                if not ocr_service.is_configured():
                    ocr_service = None
            except Exception:
                ocr_service = None
            router_service = RouterService(llm_client=llm_client)
            payment_extractor = PaymentExtractor(llm_client=llm_client)
            loan_extractor = LoanExtractor(llm_client=llm_client)
            evidence_gate = EvidenceGate()
            consolidator = ConsolidatorService()
            compute_engine = ComputeEngine()

            # 4. PIPELINE: Processar cada PDF
            payment_results: list[PaymentExtractionResult] = []
            loan_results: list[LoanContractResult] = []
            doc_sources: dict[str, DocumentSource] = {}
            payroll_records: list[PayrollMonth] = []
            loan_records: list[LoanContract] = []
            historical_records: list[HistoricalContract] = []
            inss_margin_payload: tuple[dict[str, object], UUID] | None = None

            def resolve_local_path(storage_url: str) -> Path:
                if storage_url.startswith("local://"):
                    return Path(storage_url.replace("local://", "", 1))
                return Path(storage_url)

            def is_meaningful_loan(result: LoanContractResult) -> bool:
                if result.parcela_mensal and result.parcela_mensal.value is not None:
                    return True
                if result.valor_total and result.valor_total.value is not None:
                    return True
                if result.total_parcelas is not None:
                    return True
                if result.parcelas_pagas is not None:
                    return True
                if result.parcelas_restantes is not None:
                    return True
                return False

            def to_cent(value: float | None) -> int | None:
                if value is None:
                    return None
                return int(round(value * 100))

            def infer_contract_status(alerts: list[str], explicit_status: str | None) -> str:
                if explicit_status in {
                    ContractStatus.ATIVO.value,
                    ContractStatus.QUITADO.value,
                    ContractStatus.INDEFINIDO.value,
                }:
                    return explicit_status
                text = " ".join(alerts or []).lower()
                if "encerr" in text or "exclu" in text or "quitad" in text:
                    return ContractStatus.QUITADO.value
                return ContractStatus.ATIVO.value

            def normalize_rate_for_db(value: object) -> str | None:
                if value is None:
                    return None
                raw = value
                if isinstance(raw, dict):
                    raw = raw.get("value")
                if raw is None:
                    return None
                text = str(raw).strip()
                if not text:
                    return None
                compact = text.replace(" ", "")
                match = re.fullmatch(r"(\d{1,2},\d{1,2})%?", compact)
                if match:
                    text = f"{match.group(1)}%"
                if len(text) > 20:
                    return text[:20]
                return text

            for i, file in enumerate(files):
                # Step 1: PDF Extraction (arquivo real)
                if file.storage_provider != "local" or not file.storage_url:
                    raise JobProcessingError(
                        f"Arquivo não disponível localmente: {file.id}"
                    )

                file_path = resolve_local_path(file.storage_url)
                if not file_path.exists():
                    raise JobProcessingError(f"Arquivo não encontrado: {file_path}")

                pdf_bytes = file_path.read_bytes()
                extraction = pdf_service.extract_from_bytes(
                    pdf_bytes, filename=file.original_filename
                )
                pdf_text = extraction.text
                used_ocr = False
                extraction_method = "native"

                if pdf_service.should_use_ocr(extraction.quality_score) and ocr_service:
                    try:
                        ocr_result = await ocr_service.extract_text(pdf_bytes)
                        if ocr_result.text:
                            pdf_text = ocr_result.text
                            used_ocr = True
                            extraction_method = "ocr"
                    except Exception:
                        # Se OCR falhar, continuar com extração nativa
                        pass

                # Step 2: Router (classificar documento)
                router_result = await router_service.classify_document(
                    text=pdf_text,
                    metadata={
                        "filename": file.original_filename,
                        "file_id": str(file.id),
                    },
                )

                # Step 3: Extractors (extrair dados)
                gate_result = None
                gate_status = None
                gate_alerts_payload = []
                extracted_payload = None

                if router_result.doc_family in [
                    "PAYROLL_SALARY_STATEMENT",
                    "INSS_HISTORICO_CREDITOS",
                ]:
                    # Payment Extractor
                    payment_result = await payment_extractor.extract(pdf_text)
                    extracted_payload = payment_result

                    # Step 4: Evidence Gate (validar)
                    gate_result = evidence_gate.validate_payment_extraction(
                        payment_result, document_text=pdf_text
                    )
                    gate_status = gate_result.gate_status.value
                    gate_alerts_payload = [
                        alert.__dict__ for alert in gate_result.alerts
                    ]

                    if gate_result.gate_status.value != "FAILED":
                        payment_results.append(payment_result)
                        if router_result.doc_family == "INSS_HISTORICO_CREDITOS":
                            doc_sources[f"payment_{i}"] = (
                                DocumentSource.INSS_HISTORICO_CREDITOS
                            )
                        else:
                            doc_sources[f"payment_{i}"] = (
                                DocumentSource.PAYROLL_SALARY_STATEMENT
                            )
                        payroll_records.append(
                            PayrollMonth(
                                job_id=job_id,
                                source_file_id=file.id,
                                competencia=payment_result.competencia or "1970-01",
                                bruto_cent=to_cent(payment_result.salario_bruto.value),
                                liquido_cent=to_cent(payment_result.salario_liquido.value),
                                descontos_cent=to_cent(payment_result.total_descontos.value),
                                consignado_cent=(
                                    sum(
                                        linha.valor_cent
                                        for linha in (payment_result.linhas_consignado or [])
                                    )
                                    if payment_result.linhas_consignado
                                    else None
                                ),
                                method_bruto=payment_result.salario_bruto.method,
                                method_liquido=payment_result.salario_liquido.method,
                                method_descontos=payment_result.total_descontos.method,
                                method_consignado="SUM_LINES"
                                if payment_result.linhas_consignado
                                else None,
                                evidence={
                                    "salario_bruto": (
                                        payment_result.salario_bruto.evidence.text
                                        if payment_result.salario_bruto.evidence
                                        else None
                                    ),
                                    "salario_liquido": (
                                        payment_result.salario_liquido.evidence.text
                                        if payment_result.salario_liquido.evidence
                                        else None
                                    ),
                                    "total_descontos": (
                                        payment_result.total_descontos.evidence.text
                                        if payment_result.total_descontos.evidence
                                        else None
                                    ),
                                },
                                provenance={"router_family": router_result.doc_family},
                                consignado_lines=[
                                    {
                                        "descricao": linha.descricao,
                                        "descricao_raw": (
                                            linha.descricao_raw or linha.descricao
                                        ),
                                        "descricao_canonica": (
                                            linha.descricao_canonica
                                            or linha.descricao
                                        ),
                                        "rubrica": linha.rubrica,
                                        "prazo": linha.prazo,
                                        "valor_cent": linha.valor_cent,
                                    }
                                    for linha in (payment_result.linhas_consignado or [])
                                ],
                                alerts=payment_result.alerts,
                            )
                        )

                elif router_result.doc_family in [
                    "LOAN_CONTRACT_GENERIC",
                    "INSS_EXTRATO_CONSIGNADO",
                ]:
                    gate_results: list[tuple[int, object, bool]] = []

                    if router_result.doc_family == "INSS_EXTRATO_CONSIGNADO":
                        loan_results_list = await loan_extractor.extract_many(pdf_text)
                        extracted_payload = loan_results_list
                        for idx, loan_result in enumerate(loan_results_list):
                            gate_result = evidence_gate.validate_loan_extraction(
                                loan_result
                            )
                            meaningful = is_meaningful_loan(loan_result)
                            gate_results.append((idx, gate_result, meaningful))
                            if meaningful and gate_result.gate_status.value != "FAILED":
                                loan_results.append(loan_result)
                                contract_key_raw = "|".join(
                                    [
                                        str(job_id),
                                        str(file.id),
                                        str(idx),
                                        loan_result.contract_id or "",
                                        loan_result.lender_name or "",
                                    ]
                                )
                                loan_records.append(
                                    LoanContract(
                                        job_id=job_id,
                                        source_file_id=file.id,
                                        lender_name=loan_result.lender_name,
                                        contract_id=loan_result.contract_id,
                                        contract_key=hashlib.sha1(
                                            contract_key_raw.encode("utf-8")
                                        ).hexdigest(),
                                        parcela_cent=to_cent(loan_result.parcela_mensal.value),
                                        total_parcelas=loan_result.total_parcelas,
                                        parcelas_pagas=loan_result.parcelas_pagas,
                                        parcelas_restantes=loan_result.parcelas_restantes,
                                        valor_total_cent=to_cent(loan_result.valor_total.value),
                                        status=infer_contract_status(
                                            loan_result.alerts, loan_result.status
                                        ),
                                        taxa_juros=normalize_rate_for_db(loan_result.taxa_juros),
                                        cet_mensal=loan_result.cet_mensal,
                                        cet_anual=loan_result.cet_anual,
                                        iof_cent=loan_result.iof_cent,
                                        valor_emprestado_cent=loan_result.valor_emprestado_cent,
                                        evidence={
                                            "parcela": (
                                                loan_result.parcela_mensal.evidence.text
                                                if loan_result.parcela_mensal.evidence
                                                else None
                                            ),
                                            "valor_total": (
                                                loan_result.valor_total.evidence.text
                                                if loan_result.valor_total.evidence
                                                else None
                                            ),
                                        },
                                    )
                                )
                            elif not meaningful:
                                gate_alerts_payload.append(
                                    {
                                        "field_name": f"contract[{idx}]",
                                        "extracted_value": None,
                                        "reparsed_value": None,
                                        "evidence_text": "",
                                        "reason": "Contrato sem valores extraídos",
                                        "is_critical": False,
                                        "contract_index": idx,
                                    }
                                )

                        # Extrair valores do benefício do extrato (base de cálculo / total comprometido)
                        beneficio_result = (
                            payment_extractor._extract_inss_extrato_beneficio_values(
                                pdf_text, router_result.competencias_detectadas
                            )
                        )
                        beneficio_gate = evidence_gate.validate_payment_extraction(
                            beneficio_result, document_text=pdf_text
                        )
                        for alert in beneficio_gate.alerts:
                            gate_alerts_payload.append(alert.__dict__)
                        if beneficio_gate.gate_status.value != "FAILED":
                            payment_results.append(beneficio_result)
                            doc_sources[f"payment_{i}"] = (
                                DocumentSource.INSS_EXTRATO_CONSIGNADO
                            )
                            payroll_records.append(
                                PayrollMonth(
                                    job_id=job_id,
                                    source_file_id=file.id,
                                    competencia=beneficio_result.competencia or "1970-01",
                                    bruto_cent=to_cent(beneficio_result.salario_bruto.value),
                                    liquido_cent=to_cent(beneficio_result.salario_liquido.value),
                                    descontos_cent=to_cent(
                                        beneficio_result.total_descontos.value
                                    ),
                                    consignado_cent=None,
                                    method_bruto=beneficio_result.salario_bruto.method,
                                    method_liquido=beneficio_result.salario_liquido.method,
                                    method_descontos=beneficio_result.total_descontos.method,
                                    method_consignado=None,
                                    evidence={
                                        "salario_bruto": (
                                            beneficio_result.salario_bruto.evidence.text
                                            if beneficio_result.salario_bruto.evidence
                                            else None
                                        ),
                                        "total_descontos": (
                                            beneficio_result.total_descontos.evidence.text
                                            if beneficio_result.total_descontos.evidence
                                            else None
                                        ),
                                    },
                                    provenance={"router_family": router_result.doc_family},
                                    consignado_lines=[],
                                    alerts=beneficio_result.alerts,
                                )
                            )

                        margin_data = loan_extractor.extract_inss_margin_data(pdf_text)
                        if margin_data and inss_margin_payload is None:
                            inss_margin_payload = (margin_data, file.id)

                        for historical in loan_extractor.extract_inss_historical_contracts(
                            pdf_text
                        ):
                            data_contratacao = historical.get("data_contratacao")
                            data_quitacao = historical.get("data_quitacao")
                            historical_records.append(
                                HistoricalContract(
                                    job_id=job_id,
                                    source_file_id=file.id,
                                    lender_name=(
                                        str(historical.get("lender_name"))
                                        if historical.get("lender_name")
                                        else None
                                    ),
                                    contract_id=(
                                        str(historical.get("contract_id"))
                                        if historical.get("contract_id")
                                        else None
                                    ),
                                    data_contratacao=(
                                        datetime.strptime(data_contratacao, "%Y-%m-%d").date()
                                        if isinstance(data_contratacao, str)
                                        else None
                                    ),
                                    data_quitacao=(
                                        datetime.strptime(data_quitacao, "%Y-%m-%d").date()
                                        if isinstance(data_quitacao, str)
                                        else None
                                    ),
                                    parcela_cent=(
                                        int(historical["parcela_cent"])
                                        if historical.get("parcela_cent") is not None
                                        else None
                                    ),
                                    valor_emprestado_cent=(
                                        int(historical["valor_emprestado_cent"])
                                        if historical.get("valor_emprestado_cent")
                                        is not None
                                        else None
                                    ),
                                    motivo_encerramento=(
                                        str(historical.get("motivo_encerramento"))
                                        if historical.get("motivo_encerramento")
                                        else None
                                    ),
                                )
                            )
                    else:
                        # Loan Extractor (contrato único)
                        loan_result = await loan_extractor.extract(pdf_text)
                        extracted_payload = loan_result

                        # Validar
                        gate_result = evidence_gate.validate_loan_extraction(
                            loan_result
                        )
                        meaningful = is_meaningful_loan(loan_result)
                        gate_results.append((0, gate_result, meaningful))

                        if meaningful and gate_result.gate_status.value != "FAILED":
                            loan_results.append(loan_result)
                            contract_key_raw = "|".join(
                                [
                                    str(job_id),
                                    str(file.id),
                                    "0",
                                    loan_result.contract_id or "",
                                    loan_result.lender_name or "",
                                ]
                            )
                            loan_records.append(
                                LoanContract(
                                    job_id=job_id,
                                    source_file_id=file.id,
                                    lender_name=loan_result.lender_name,
                                    contract_id=loan_result.contract_id,
                                    contract_key=hashlib.sha1(
                                        contract_key_raw.encode("utf-8")
                                    ).hexdigest(),
                                    parcela_cent=to_cent(loan_result.parcela_mensal.value),
                                    total_parcelas=loan_result.total_parcelas,
                                    parcelas_pagas=loan_result.parcelas_pagas,
                                    parcelas_restantes=loan_result.parcelas_restantes,
                                    valor_total_cent=to_cent(loan_result.valor_total.value),
                                    status=infer_contract_status(
                                        loan_result.alerts, loan_result.status
                                    ),
                                    taxa_juros=normalize_rate_for_db(loan_result.taxa_juros),
                                    cet_mensal=loan_result.cet_mensal,
                                    cet_anual=loan_result.cet_anual,
                                    iof_cent=loan_result.iof_cent,
                                    valor_emprestado_cent=loan_result.valor_emprestado_cent,
                                    evidence={
                                        "parcela": (
                                            loan_result.parcela_mensal.evidence.text
                                            if loan_result.parcela_mensal.evidence
                                            else None
                                        ),
                                        "valor_total": (
                                            loan_result.valor_total.evidence.text
                                            if loan_result.valor_total.evidence
                                            else None
                                        ),
                                    },
                                )
                            )
                        elif not meaningful:
                            gate_alerts_payload.append(
                                {
                                    "field_name": "contract[0]",
                                    "extracted_value": None,
                                    "reparsed_value": None,
                                    "evidence_text": "",
                                    "reason": "Contrato sem valores extraídos",
                                    "is_critical": False,
                                    "contract_index": 0,
                                }
                            )

                    # Agregar gate_status e alertas quando há múltiplos contratos
                    if gate_results:
                        has_meaningful = any(m for _, _, m in gate_results)
                        has_passed = any(
                            gr.gate_status.value == "PASSED" and m
                            for _, gr, m in gate_results
                        )
                        has_warn = any(
                            gr.gate_status.value == "WARN" and m
                            for _, gr, m in gate_results
                        )
                        if has_passed:
                            gate_status = "PASSED"
                        elif has_warn:
                            gate_status = "WARN"
                        elif has_meaningful:
                            gate_status = "FAILED"
                        else:
                            gate_status = "FAILED"
                            gate_alerts_payload.append(
                                {
                                    "field_name": "contratos",
                                    "extracted_value": None,
                                    "reparsed_value": None,
                                    "evidence_text": "",
                                    "reason": "Nenhum contrato válido foi extraído",
                                    "is_critical": False,
                                }
                            )

                        for idx, gr, _ in gate_results:
                            for alert in gr.alerts:
                                payload = alert.__dict__.copy()
                                payload["contract_index"] = idx
                                gate_alerts_payload.append(payload)

                # Persistir extração para auditoria
                from dataclasses import asdict, is_dataclass

                extracted_json = None
                if extracted_payload is not None:
                    if is_dataclass(extracted_payload):
                        extracted_json = asdict(extracted_payload)
                    elif isinstance(extracted_payload, list):
                        extracted_json = [
                            asdict(item) if is_dataclass(item) else item
                            for item in extracted_payload
                        ]
                    else:
                        extracted_json = extracted_payload

                evidence_json = (
                    [e.__dict__ for e in router_result.evidence]
                    if router_result.evidence
                    else []
                )

                extraction_record = DocumentExtraction(
                    file_id=file.id,
                    extractor_version="1.0",
                    router_family=router_result.doc_family,
                    router_confidence=router_result.confidence,
                    capabilities=router_result.capabilities,
                    competencias_detectadas=router_result.competencias_detectadas,
                    text_quality_score=extraction.quality_score,
                    used_ocr=used_ocr,
                    extraction_method=extraction_method,
                    extracted_json=extracted_json,
                    evidence_json=evidence_json,
                    gate_status=gate_status,
                    gate_alerts=gate_alerts_payload,
                    processing_time_ms=extraction.extraction_time_ms,
                    extraction_metadata={
                        "file_name": file.original_filename,
                        "page_count": extraction.page_count,
                        "file_size_bytes": extraction.file_size_bytes,
                    },
                )
                db.add(extraction_record)

            for payroll_record in payroll_records:
                db.add(payroll_record)

            for loan_record in loan_records:
                loan_record.calculate_missing_fields()
                db.add(loan_record)

            for historical_record in historical_records:
                db.add(historical_record)

            if inss_margin_payload:
                margin_data, source_file_id = inss_margin_payload
                db.add(
                    INSSMargin(
                        job_id=job_id,
                        source_file_id=source_file_id,
                        base_calculo_cent=margin_data.get("base_calculo_cent"),
                        max_comprometimento_cent=margin_data.get(
                            "max_comprometimento_cent"
                        ),
                        total_comprometido_cent=margin_data.get("total_comprometido_cent"),
                        margem_emprestimo_cent=margin_data.get("margem_emprestimo_cent"),
                        margem_rmc_cent=margin_data.get("margem_rmc_cent"),
                        margem_rcc_cent=margin_data.get("margem_rcc_cent"),
                        cet_mensal=margin_data.get("cet_mensal"),
                        cet_anual=margin_data.get("cet_anual"),
                        rmc_banco=margin_data.get("rmc_banco"),
                        rmc_limite_cent=margin_data.get("rmc_limite_cent"),
                        rmc_reservado_cent=margin_data.get("rmc_reservado_cent"),
                        evidence=margin_data.get("evidence"),
                    )
                )

            # 5. Consolidator (resolver conflitos)
            if not payment_results and not loan_results:
                raise JobProcessingError(
                    "Nenhum documento validado pelo Evidence Gate"
                )

            consolidated = consolidator.consolidate(
                payment_results=payment_results,
                loan_results=loan_results,
                doc_sources=doc_sources,
                renda_mensal_declarada_cent=job.renda_mensal_declarada_cent,
                gasto_dividas_declarado_cent=job.gasto_dividas_declarado_cent,
            )

            # Atualizar competência alvo no job
            job.competencia_alvo = consolidated.competencia_alvo

            # 6. Compute Engine (calcular outputs)
            compute_result = compute_engine.compute(consolidated)

            # 6b. Gerar ofertas do produto (baseado no salário líquido)
            offers_alerts: list[str] = []
            offers_payload: list[Offer] = []
            inss_margin_data = inss_margin_payload[0] if inss_margin_payload else None
            salary_cent, salary_source = resolve_offer_salary_cent(
                compute_salario_liquido_cent=compute_result.salario_liquido_cent,
                renda_mensal_declarada_cent=job.renda_mensal_declarada_cent,
                perfil_dados=consolidated.perfil_dados,
                inss_margin_data=inss_margin_data,
            )
            if salary_source == "BENEFICIO_LIQUIDO_EXTRATO":
                offers_alerts.append(
                    "Ofertas geradas com base no benefício líquido estimado do extrato"
                )
            is_qualified, qualification_base_cent, qualification_source = is_offer_qualified(
                compute_salario_liquido_cent=compute_result.salario_liquido_cent,
                perfil_dados=consolidated.perfil_dados,
                inss_margin_data=inss_margin_data,
            )
            if not is_qualified:
                base_label = (
                    f"{qualification_base_cent / 100:.2f}" if qualification_base_cent is not None else "--"
                ).replace(".", ",")
                min_label = f"{MIN_OFFER_QUALIFICATION_CENT / 100:.2f}".replace(".", ",")
                offers_alerts.append(
                    f"Lead não qualificado para ofertas: base {base_label} (< {min_label}) via {qualification_source}"
                )

            product = None
            if job.product_id:
                product_result = await db.execute(
                    select(Product).where(Product.id == job.product_id)
                )
                product = product_result.scalar_one_or_none()

            if product and is_qualified:
                offers, generated_alerts = generate_offers(
                    job_id=job_id,
                    salary_cent=salary_cent,
                    product=product,
                )
                offers_alerts.extend(generated_alerts)
                for offer in offers:
                    offers_payload.append(
                        Offer(
                            job_id=job_id,
                            product_id=product.id,
                            kind=offer.kind,
                            installment_count=offer.installment_count,
                            installment_value_cent=offer.installment_value_cent,
                            total_value_cent=offer.total_value_cent,
                            entry_value_cent=offer.entry_value_cent,
                            entry_due_days=offer.entry_due_days,
                            first_payment_days=offer.first_payment_days,
                            payment_method=offer.payment_method,
                            salary_liquid_used_cent=offer.salary_liquid_used_cent,
                            percent_used=offer.percent_used,
                            seed=f"{job_id}:{offer.kind}",
                            text=offer.text,
                        )
                    )
            elif not product:
                offers_alerts.append("Ofertas não geradas: produto não informado")

            # 7. Persistir resultado final
            # Alertas não devem ser retornados no resultado final.
            alerts_payload: list[str] = []

            final_result = FinalResult(
                job_id=job_id,
                competencia_alvo=consolidated.competencia_alvo,
                salario_bruto_cent=compute_result.salario_bruto_cent,
                salario_liquido_cent=compute_result.salario_liquido_cent,
                total_descontos_cent=compute_result.total_descontos_cent,
                divida_mensal_cent=compute_result.divida_mensal_cent,
                divida_mensal_reduzida_cent=compute_result.divida_mensal_reduzida_cent,
                consignado_mensal_cent=compute_result.consignado_mensal_cent,
                divida_total_consignada_cent=compute_result.divida_total_consignada_cent,
                divida_total_reduzida_cent=compute_result.divida_total_reduzida_cent,
                parcelas_restantes_total=compute_result.parcelas_restantes_total,
                calculation_methods={
                    "total_descontos": compute_result.descontos_method,
                    "divida_mensal": compute_result.divida_mensal_method,
                    "divida_mensal_reduzida": compute_result.divida_mensal_reduzida_method,
                    "consignado_mensal": compute_result.consignado_method,
                    "divida_total": compute_result.divida_method,
                    "divida_total_reduzida": compute_result.divida_total_reduzida_method,
                    "parcelas_restantes": compute_result.parcelas_method,
                },
                provenance={
                    "salario_bruto": {"source": compute_result.bruto_source},
                    "salario_liquido": {"source": compute_result.liquido_source},
                    "total_descontos": {
                        "source": (
                            consolidated.total_descontos.source.value
                            if consolidated.total_descontos
                            else None
                        )
                    },
                },
                alerts=alerts_payload,
            )

            db.add(final_result)
            for offer in offers_payload:
                db.add(offer)

            # 8. Atualizar job para SUCCEEDED
            job.status = JobStatus.SUCCEEDED.value
            job.completed_at = datetime.now(timezone.utc)

            # Calcular tempo de processamento
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            job.processing_time_ms = int(processing_time)

            await db.commit()

            return {
                "job_id": str(job_id),
                "status": "SUCCEEDED",
                "competencia_alvo": consolidated.competencia_alvo,
                "processing_time_ms": int(processing_time),
                "alerts": len(compute_result.alerts),
            }
    except Exception as e:
        # Em caso de erro, atualizar job para FAILED
        try:
            async with session_maker() as db:
                result = await db.execute(
                    select(AnalysisJob).where(AnalysisJob.id == job_id)
                )
                job = result.scalar_one_or_none()
                if job:
                    job.status = JobStatus.FAILED.value
                    job.error_code = "PROCESSING_ERROR"
                    job.error_message = str(e)[:500]  # Truncar mensagem
                    job.completed_at = datetime.now(timezone.utc)

                    processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                    job.processing_time_ms = int(processing_time)

                    await db.commit()
        except Exception:
            # Se não conseguir atualizar o job, apenas logar
            pass

        raise JobProcessingError(f"Failed to process job {job_id}: {str(e)}") from e
    finally:
        await engine.dispose()


# Helper function para enfileirar job
async def enqueue_job(job_id: UUID) -> str:
    """
    Enfileira um job para processamento assíncrono.

    Args:
        job_id: UUID do job

    Returns:
        Task ID do Celery
    """
    task = process_job_task.delay(str(job_id))
    return task.id
