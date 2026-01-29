"""
Celery Tasks
~~~~~~~~~~~~

Tasks assíncronas para processamento de jobs de análise.
"""

import asyncio
from datetime import datetime
from uuid import UUID

from celery import Task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.final_result import FinalResult
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

    # IMPORTANTE: Dispor do engine antes de criar novo event loop
    # Isso força a criação de novas conexões no novo event loop
    from app.core.database import engine

    async def _dispose_and_run():
        # Dispor de todas as conexões existentes
        await engine.dispose()
        # Executar o pipeline
        return await _process_job_async(job_uuid, self)

    # Executar pipeline assíncrono com novo event loop
    result = asyncio.run(_dispose_and_run())

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
    start_time = datetime.now()

    async with async_session_maker() as db:
        try:
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
            # NOTA: Em produção, usar LLMClient real. Para testes, usar MockLLMClient
            use_mock = True  # TODO: Configurar via env var
            llm_client = MockLLMClient() if use_mock else LLMClient()

            pdf_service = PDFExtractionService()
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

            for i, file in enumerate(files):
                # Step 1: PDF Extraction
                # NOTA: Em produção, baixar PDF do S3
                # Por enquanto, criar texto mockado
                pdf_text = f"FOLHA DE PAGAMENTO\nCompetência: 01/2024\n\nPROVENTOS\nTotal de Proventos: R$ 5.500,00\n\nDESCONTOS\nTotal de Descontos: R$ 1.385,00\n\nLÍQUIDO A RECEBER: R$ 4.115,00\n\nConsignado Banco ABC (216): R$ 250,00"

                # Step 2: Router (classificar documento)
                router_result = await router_service.classify_document(
                    text=pdf_text,
                    metadata={
                        "filename": file.original_filename,
                        "file_id": str(file.id),
                    },
                )

                # Step 3: Extractors (extrair dados)
                if router_result.doc_family == "PAYROLL_SALARY_STATEMENT":
                    # Payment Extractor
                    payment_result = await payment_extractor.extract(pdf_text)

                    # Step 4: Evidence Gate (validar)
                    gate_result = evidence_gate.validate_payment_extraction(payment_result)

                    if gate_result.gate_status.value != "FAILED":
                        payment_results.append(payment_result)
                        doc_sources[f"payment_{i}"] = DocumentSource.PAYROLL_SALARY_STATEMENT

                elif "LOAN" in router_result.doc_family:
                    # Loan Extractor
                    loan_result = await loan_extractor.extract(pdf_text)

                    # Validar
                    gate_result = evidence_gate.validate_loan_extraction(loan_result)

                    if gate_result.gate_status.value != "FAILED":
                        loan_results.append(loan_result)

            # 5. Consolidator (resolver conflitos)
            consolidated = consolidator.consolidate(
                payment_results=payment_results,
                loan_results=loan_results,
                doc_sources=doc_sources,
                renda_mensal_declarada_cent=job.renda_mensal_declarada_cent,
            )

            # Atualizar competência alvo no job
            job.competencia_alvo = consolidated.competencia_alvo

            # 6. Compute Engine (calcular outputs)
            compute_result = compute_engine.compute(consolidated)

            # 7. Persistir resultado final
            final_result = FinalResult(
                job_id=job_id,
                competencia_alvo=consolidated.competencia_alvo,
                salario_bruto_cent=compute_result.salario_bruto_cent,
                salario_liquido_cent=compute_result.salario_liquido_cent,
                total_descontos_cent=compute_result.total_descontos_cent,
                consignado_mensal_cent=compute_result.consignado_mensal_cent,
                divida_total_consignada_cent=compute_result.divida_total_consignada_cent,
                parcelas_restantes_total=compute_result.parcelas_restantes_total,
                calculation_methods={
                    "total_descontos": compute_result.descontos_method,
                    "consignado_mensal": compute_result.consignado_method,
                    "divida_total": compute_result.divida_method,
                    "parcelas_restantes": compute_result.parcelas_method,
                },
                provenance={
                    "salario_bruto": {"source": compute_result.bruto_source},
                    "salario_liquido": {"source": compute_result.liquido_source},
                },
                alerts=[],  # TODO: Adicionar alertas do Evidence Gate
            )

            db.add(final_result)

            # 8. Atualizar job para SUCCEEDED
            job.status = JobStatus.SUCCEEDED.value
            job.completed_at = datetime.now()

            # Calcular tempo de processamento
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
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
            await db.rollback()

            try:
                job.status = JobStatus.FAILED.value
                job.error_code = "PROCESSING_ERROR"
                job.error_message = str(e)[:500]  # Truncar mensagem
                job.completed_at = datetime.now()

                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                job.processing_time_ms = int(processing_time)

                await db.commit()
            except Exception:
                # Se não conseguir atualizar o job, apenas logar
                pass

            raise JobProcessingError(f"Failed to process job {job_id}: {str(e)}") from e


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
