#!/usr/bin/env python3
"""
Teste das Celery Tasks.
"""

import asyncio
import sys
import uuid


async def test_task_imports():
    """Testa se os imports das tasks funcionam."""
    print("=" * 60)
    print("Teste 1: Imports das Tasks")
    print("=" * 60)

    try:
        from app.workers.celery_app import celery_app
        from app.workers.tasks import enqueue_job, process_job_task

        print("\n✅ Todos os imports bem-sucedidos")
        print(f"   - Celery app: {celery_app.main}")
        print(f"   - Task process_job: {process_job_task.name}")
        print(f"   - Helper enqueue_job: {enqueue_job.__name__}")

        return True
    except Exception as e:
        print(f"\n❌ Erro nos imports: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_celery_config():
    """Testa configuração do Celery."""
    print("\n" + "=" * 60)
    print("Teste 2: Configuração do Celery")
    print("=" * 60)

    try:
        from app.workers.celery_app import celery_app

        print("\n📋 Configurações:")
        print(f"   - Broker: {celery_app.conf.broker_url[:50]}...")
        print(f"   - Backend: {celery_app.conf.result_backend[:50]}...")
        print(f"   - Timezone: {celery_app.conf.timezone}")
        print(f"   - Task serializer: {celery_app.conf.task_serializer}")
        print(f"   - Time limit: {celery_app.conf.task_time_limit}s")

        # Verificar tasks registradas
        registered_tasks = list(celery_app.tasks.keys())
        print(f"\n🎯 Tasks registradas: {len(registered_tasks)}")
        for task_name in registered_tasks:
            if "process_job" in task_name:
                print(f"   ✅ {task_name}")

        return True
    except Exception as e:
        print(f"\n❌ Erro na configuração: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_pipeline_structure():
    """Testa estrutura do pipeline de processamento."""
    print("\n" + "=" * 60)
    print("Teste 3: Estrutura do Pipeline")
    print("=" * 60)

    try:
        from app.workers.tasks import _process_job_async

        print("\n📊 Componentes do pipeline:")

        # Verificar imports de services
        from app.services.compute_engine import ComputeEngine
        from app.services.consolidator import ConsolidatorService
        from app.services.evidence_gate import EvidenceGate
        from app.services.extractors import LoanExtractor, PaymentExtractor
        from app.services.llm_client import MockLLMClient
        from app.services.pdf_extraction import PDFExtractionService
        from app.services.router import RouterService

        services = [
            ("PDF Extraction", PDFExtractionService),
            ("Router", RouterService),
            ("Payment Extractor", PaymentExtractor),
            ("Loan Extractor", LoanExtractor),
            ("Evidence Gate", EvidenceGate),
            ("Consolidator", ConsolidatorService),
            ("Compute Engine", ComputeEngine),
            ("Mock LLM Client", MockLLMClient),
        ]

        for service_name, service_class in services:
            print(f"   ✅ {service_name}: {service_class.__name__}")

        return True
    except Exception as e:
        print(f"\n❌ Erro na estrutura: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_job_states():
    """Testa transições de estado do job."""
    print("\n" + "=" * 60)
    print("Teste 4: Estados do Job")
    print("=" * 60)

    try:
        from app.models.analysis_job import JobStatus

        print("\n📌 Estados possíveis:")
        states = [
            JobStatus.PENDING,
            JobStatus.RUNNING,
            JobStatus.SUCCEEDED,
            JobStatus.FAILED,
        ]

        for state in states:
            print(f"   ✅ {state.value}")

        # Verificar fluxo esperado
        print("\n🔄 Fluxo de processamento:")
        print("   1. PENDING  → Job criado, aguardando processamento")
        print("   2. RUNNING  → Task iniciada, processando pipeline")
        print("   3. SUCCEEDED ou FAILED → Task concluída")

        return True
    except Exception as e:
        print(f"\n❌ Erro nos estados: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_error_handling():
    """Testa tratamento de erros."""
    print("\n" + "=" * 60)
    print("Teste 5: Tratamento de Erros")
    print("=" * 60)

    try:
        from app.workers.tasks import JobProcessingError

        print("\n🚨 Tipos de erro:")
        print(f"   ✅ JobProcessingError: {JobProcessingError.__name__}")

        # Testar criação de erro
        try:
            raise JobProcessingError("Test error")
        except JobProcessingError as e:
            print(f"   ✅ Erro capturado: {str(e)}")

        print("\n📝 Comportamento esperado:")
        print("   - Job ID inválido → JobProcessingError")
        print("   - Job não encontrado → JobProcessingError")
        print("   - Erro no pipeline → Job marcado como FAILED")
        print("   - Error code e message salvos no banco")

        return True
    except Exception as e:
        print(f"\n❌ Erro no tratamento: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Executa todos os testes."""
    try:
        # Teste 1: Imports
        result1 = await test_task_imports()

        # Teste 2: Configuração
        result2 = await test_celery_config()

        # Teste 3: Pipeline
        result3 = await test_pipeline_structure()

        # Teste 4: Estados
        result4 = await test_job_states()

        # Teste 5: Erros
        result5 = await test_error_handling()

        # Resultado final
        print("\n" + "=" * 60)
        all_passed = result1 and result2 and result3 and result4 and result5
        if all_passed:
            print("✅ Todos os testes das Celery Tasks passaram!")
        else:
            print("❌ Alguns testes falharam")
        print("=" * 60)

        print("\n📌 Nota:")
        print("   Para testar o processamento completo, é necessário:")
        print("   1. Ter Redis rodando (broker/backend)")
        print("   2. Iniciar worker Celery: celery -A app.workers.celery_app worker")
        print("   3. Criar job via API e aguardar processamento")

        return all_passed

    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
