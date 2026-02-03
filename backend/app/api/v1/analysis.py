"""
Analysis Job API Endpoints
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Endpoints para criar e consultar jobs de análise de documentos.
Baseado em PRD RF-013, RF-014, RF-015.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.final_result import FinalResult
from app.models.offer import Offer
from app.models.product import Product
from app.models.uploaded_file import UploadedFile
from app.schemas.analysis_job import AnalysisJobCreate, AnalysisJobResponse
from app.schemas.final_result import Evidence, FinalResultResponse, MonetaryField
from app.schemas.offer import OfferResponse
router = APIRouter(prefix="/analysis", tags=["Analysis"])


# ==============================================
# POST /v1/analysis/jobs - Criar Job
# ==============================================
@router.post(
    "/jobs",
    response_model=AnalysisJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar job de análise",
    description="Upload de PDFs e dados declarados para criar novo job de análise",
)
async def create_analysis_job(
    files: Annotated[
        list[UploadFile],
        File(
            description="Arquivos PDF (1-3 arquivos, max 10MB cada)",
            media_type="application/pdf",
        ),
    ],
    product_id: Annotated[
        str,
        Form(description="ID do produto selecionado"),
    ],
    renda_mensal_declarada: Annotated[
        str | None,
        Form(description="Renda mensal declarada (formato: 2500.00)"),
    ] = None,
    gasto_dividas_declarado: Annotated[
        str | None,
        Form(description="Gasto mensal com dívidas declarado (formato: 800.00)"),
    ] = None,
    db: AsyncSession = Depends(get_db),
) -> AnalysisJobResponse:
    """
    Cria novo job de análise (RF-013).

    Validações:
    - 1-3 arquivos PDF
    - Cada arquivo <= 10MB
    - Total <= 25MB
    - Formato .pdf

    Returns:
        201 Created com jobId e status PENDING
    """
    # Validar número de arquivos (RF-013 CA-002)
    if not files or len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 1 PDF file is required",
        )

    if len(files) > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 3 PDF files allowed",
        )

    # Validar arquivos
    total_size = 0
    for file in files:
        # Validar extensão
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file format. PDF required: {file.filename}",
            )

        # Validar tamanho (10MB = 10 * 1024 * 1024 bytes)
        content = await file.read()
        file_size = len(content)
        total_size += file_size

        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds 10MB: {file.filename}",
            )

        # Reset file pointer para próxima leitura
        await file.seek(0)

    # Validar tamanho total (25MB)
    if total_size > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total file size exceeds 25MB",
        )

    # Parsear valores declarados (RF-013 CA-003)
    renda_mensal_declarada_cent = None
    gasto_dividas_declarado_cent = None

    # Validar produto
    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid product_id: {str(e)}",
        ) from e

    product_result = await db.execute(
        select(Product).where(Product.id == product_uuid, Product.active.is_(True))
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product not found or inactive",
        )

    if renda_mensal_declarada:
        try:
            # Usar o validator do schema
            job_create = AnalysisJobCreate(
                renda_mensal_declarada=renda_mensal_declarada
            )
            renda_mensal_declarada_cent = int(
                float(job_create.renda_mensal_declarada or "0") * 100
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid renda_mensal_declarada: {str(e)}",
            )

    if gasto_dividas_declarado:
        try:
            job_create = AnalysisJobCreate(
                gasto_dividas_declarado=gasto_dividas_declarado
            )
            gasto_dividas_declarado_cent = int(
                float(job_create.gasto_dividas_declarado or "0") * 100
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid gasto_dividas_declarado: {str(e)}",
            )

    # Criar job (RF-013 RN-001)
    job_id = uuid.uuid4()
    job = AnalysisJob(
        id=job_id,
        user_id=None,  # TODO: Extrair de JWT quando autenticação estiver implementada
        status=JobStatus.PENDING,
        product_id=product_uuid,
        renda_mensal_declarada_cent=renda_mensal_declarada_cent,
        gasto_dividas_declarado_cent=gasto_dividas_declarado_cent,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.add(job)

    # TODO: Upload PDFs para S3 (RF-013 RN-003)
    # Por enquanto, apenas criar registros de arquivos
    import hashlib

    base_dir = Path(settings.local_storage_path)
    if not base_dir.is_absolute():
        base_dir = Path.cwd() / base_dir
    job_dir = base_dir / "jobs" / str(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)

    for i, file in enumerate(files):
        file_id = uuid.uuid4()
        file_content = await file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        file_path = (job_dir / f"{file_id}.pdf").resolve()
        file_path.write_bytes(file_content)

        uploaded_file = UploadedFile(
            id=file_id,
            job_id=job_id,
            original_filename=file.filename or f"document_{i}.pdf",
            file_size=len(file_content),
            mime_type=file.content_type or "application/pdf",
            file_sha256=file_hash,
            storage_url=f"local://{file_path}",
            storage_provider="local",
        )
        await file.seek(0)  # Reset
        db.add(uploaded_file)

    # Persistir no banco
    await db.commit()
    await db.refresh(job)

    # Enfileirar job no Celery para processamento assíncrono (RF-013 passo 6)
    try:
        from app.workers.tasks import enqueue_job

        task_id = await enqueue_job(job_id)
        print(f"Job {job_id} enqueued with task_id: {task_id}")
    except Exception as e:
        # Se falhar ao enfileirar, logar mas não falhar o request
        # O job ficará PENDING e pode ser re-enfileirado manualmente
        print(f"Failed to enqueue job {job_id}: {e}")

    return AnalysisJobResponse.model_validate(job)


# ==============================================
# GET /v1/analysis/jobs/{jobId} - Status
# ==============================================
@router.get(
    "/jobs/{job_id}",
    response_model=AnalysisJobResponse,
    summary="Consultar status do job",
    description="Obtém status atual e progresso do job de análise",
)
async def get_job_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AnalysisJobResponse:
    """
    Consulta status de um job (RF-014).

    Returns:
        200 OK com status atual
        404 Not Found se jobId não existir
    """
    # Consultar job (RF-014 CA-001)
    result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )

    return AnalysisJobResponse.model_validate(job)


# ==============================================
# GET /v1/analysis/jobs/{jobId}/result - Resultado
# ==============================================
@router.get(
    "/jobs/{job_id}/result",
    response_model=FinalResultResponse,
    summary="Obter resultado final",
    description="Obtém os 6 outputs consolidados com evidências",
)
async def get_job_result(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> FinalResultResponse:
    """
    Obtém resultado final de um job (RF-015).

    Returns:
        200 OK quando status=SUCCEEDED
        202 Accepted quando status=PENDING/RUNNING
        500 Internal Server Error quando status=FAILED
        404 Not Found se jobId não existir
    """
    # Consultar job (RF-015 CA-004, CA-005)
    result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )

    # Verificar status (RF-015 CA-004)
    if job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "message": "Job is still processing",
                "status": job.status.value,
                "job_id": str(job_id),
            },
        )

    # Verificar falha (RF-015 CA-005)
    if job.status == JobStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": job.error_message or "Job processing failed",
                "error_code": job.error_code,
                "job_id": str(job_id),
            },
        )

    # Consultar resultado final (RF-015 CA-001)
    result = await db.execute(
        select(FinalResult).where(FinalResult.job_id == job_id)
    )
    final_result = result.scalar_one_or_none()

    if not final_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Result not found for job: {job_id}",
        )

    # Montar response (RF-015 CA-002)
    # Converter centavos para moeda (RF-015 RN-001)
    def cents_to_currency(cents: int | None) -> float | None:
        return cents / 100.0 if cents is not None else None

    # TODO: Buscar evidências reais do banco de dados
    # Por enquanto, retornar dados mockados
    dummy_evidence = Evidence(
        file_id=uuid.uuid4(),
        page=0,
        text="Evidência mockada (implementação completa pendente)",
    )

    # Acessar provenance e calculation_methods dos campos JSONB
    provenance = final_result.provenance or {}
    calculation_methods = final_result.calculation_methods or {}

    bruto_source = provenance.get("salario_bruto", {}).get("source", "PAYROLL")
    liquido_source = provenance.get("salario_liquido", {}).get("source", "PAYROLL")
    descontos_source = provenance.get("total_descontos", {}).get("source", bruto_source)

    offers_result = await db.execute(select(Offer).where(Offer.job_id == job_id))
    offers = offers_result.scalars().all()
    offers_sorted = sorted(
        offers,
        key=lambda offer: ["PRINCIPAL", "REDUZIDA", "SUPER"].index(offer.kind)
        if offer.kind in ["PRINCIPAL", "REDUZIDA", "SUPER"]
        else 999,
    )

    response = FinalResultResponse(
        job_id=job_id,
        competencia_alvo=job.competencia_alvo or "2024-01",
        salario_bruto=MonetaryField(
            value=cents_to_currency(final_result.salario_bruto_cent),
            currency="BRL",
            source=bruto_source,
            evidence=dummy_evidence if final_result.salario_bruto_cent else None,
            method="EXTRACTED",
        ),
        salario_liquido=MonetaryField(
            value=cents_to_currency(final_result.salario_liquido_cent),
            currency="BRL",
            source=liquido_source,
            evidence=dummy_evidence if final_result.salario_liquido_cent else None,
            method="USER_DECLARED" if liquido_source == "DECLARADO" else "EXTRACTED",
        ),
        total_descontos=MonetaryField(
            value=cents_to_currency(final_result.total_descontos_cent),
            currency="BRL",
            source=descontos_source,
            evidence=dummy_evidence if final_result.total_descontos_cent else None,
            method=calculation_methods.get("total_descontos", "COMPUTED"),
        ),
        divida_mensal=MonetaryField(
            value=cents_to_currency(final_result.divida_mensal_cent),
            currency="BRL",
            source=bruto_source,
            evidence=dummy_evidence if final_result.divida_mensal_cent else None,
            method=calculation_methods.get("divida_mensal", "COMPUTED"),
        ),
        divida_mensal_reduzida=MonetaryField(
            value=cents_to_currency(final_result.divida_mensal_reduzida_cent),
            currency="BRL",
            source=bruto_source,
            evidence=dummy_evidence
            if final_result.divida_mensal_reduzida_cent
            else None,
            method=calculation_methods.get("divida_mensal_reduzida", "COMPUTED"),
        ),
        consignado_mensal=MonetaryField(
            value=cents_to_currency(final_result.consignado_mensal_cent),
            currency="BRL",
            source=bruto_source,
            evidence=dummy_evidence if final_result.consignado_mensal_cent else None,
            method=calculation_methods.get("consignado_mensal", "COMPUTED"),
        ),
        divida_total_consignada=MonetaryField(
            value=cents_to_currency(final_result.divida_total_consignada_cent),
            currency="BRL",
            source="LOAN_CONTRACT",
            evidence=dummy_evidence
            if final_result.divida_total_consignada_cent
            else None,
            method=calculation_methods.get("divida_total", "COMPUTED"),
        ),
        divida_total_reduzida=MonetaryField(
            value=cents_to_currency(final_result.divida_total_reduzida_cent),
            currency="BRL",
            source="LOAN_CONTRACT",
            evidence=dummy_evidence
            if final_result.divida_total_reduzida_cent
            else None,
            method=calculation_methods.get("divida_total_reduzida", "COMPUTED"),
        ),
        parcelas_restantes_total=final_result.parcelas_restantes_total,
        alerts=final_result.alerts or [],
        offers=[OfferResponse.model_validate(offer) for offer in offers_sorted],
    )

    return response
