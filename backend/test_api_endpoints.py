#!/usr/bin/env python3
"""
Teste dos API Endpoints.
"""

import asyncio
import sys
from io import BytesIO


async def test_api_imports():
    """Testa se os imports da API funcionam."""
    print("=" * 60)
    print("Teste 1: Imports da API")
    print("=" * 60)

    try:
        from app.api.v1.analysis import router
        from app.api.v1.router import api_router
        from app.main import app

        print("\n✅ Todos os imports bem-sucedidos")
        print(f"   - Router de análise: {router.prefix}")
        print(f"   - API router principal: {api_router}")
        print(f"   - FastAPI app: {app.title}")

        return True
    except Exception as e:
        print(f"\n❌ Erro nos imports: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_api_structure():
    """Testa estrutura dos endpoints."""
    print("\n" + "=" * 60)
    print("Teste 2: Estrutura dos Endpoints")
    print("=" * 60)

    from app.main import app

    # Verificar rotas registradas
    routes = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes.append((route.path, list(route.methods)))

    print("\n📍 Rotas registradas:")
    for path, methods in sorted(routes):
        methods_str = ", ".join(sorted(methods))
        print(f"   {methods_str:10} {path}")

    # Verificar endpoints esperados
    expected_endpoints = [
        ("/v1/analysis/jobs", "POST"),
        ("/v1/analysis/jobs/{job_id}", "GET"),
        ("/v1/analysis/jobs/{job_id}/result", "GET"),
    ]

    checks = []
    for path, method in expected_endpoints:
        found = any(
            route_path == path and method in route_methods
            for route_path, route_methods in routes
        )
        checks.append((f"{method} {path}", found))

    print("\n🎯 Endpoints esperados:")
    all_passed = True
    for endpoint, found in checks:
        status = "✅" if found else "❌"
        print(f"   {status} {endpoint}")
        if not found:
            all_passed = False

    return all_passed


async def test_openapi_schema():
    """Testa geração do schema OpenAPI."""
    print("\n" + "=" * 60)
    print("Teste 3: Schema OpenAPI")
    print("=" * 60)

    try:
        from app.main import app

        # Gerar schema OpenAPI
        openapi_schema = app.openapi()

        print(f"\n📄 OpenAPI v{openapi_schema.get('openapi', 'N/A')}")
        print(f"   Título: {openapi_schema.get('info', {}).get('title', 'N/A')}")
        print(f"   Versão: {openapi_schema.get('info', {}).get('version', 'N/A')}")

        # Verificar paths
        paths = openapi_schema.get("paths", {})
        print(f"\n🛤️  Paths definidos: {len(paths)}")
        for path in sorted(paths.keys()):
            if "/v1/analysis" in path:
                methods = list(paths[path].keys())
                print(f"   - {path}: {', '.join(methods).upper()}")

        # Verificar schemas
        schemas = openapi_schema.get("components", {}).get("schemas", {})
        print(f"\n📦 Schemas definidos: {len(schemas)}")

        expected_schemas = [
            "AnalysisJobResponse",
            "FinalResultResponse",
            "MonetaryField",
            "Evidence",
        ]

        for schema_name in expected_schemas:
            found = schema_name in schemas
            status = "✅" if found else "❌"
            print(f"   {status} {schema_name}")

        return True
    except Exception as e:
        print(f"\n❌ Erro ao gerar schema: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_database_models():
    """Testa se os modelos do banco estão acessíveis."""
    print("\n" + "=" * 60)
    print("Teste 4: Modelos do Banco de Dados")
    print("=" * 60)

    try:
        from app.models.analysis_job import AnalysisJob, JobStatus
        from app.models.final_result import FinalResult
        from app.models.uploaded_file import UploadedFile

        print("\n✅ Modelos importados com sucesso")
        print(f"   - AnalysisJob: {AnalysisJob.__tablename__}")
        print(f"   - FinalResult: {FinalResult.__tablename__}")
        print(f"   - UploadedFile: {UploadedFile.__tablename__}")
        print(f"   - JobStatus enum: {[s.value for s in JobStatus]}")

        return True
    except Exception as e:
        print(f"\n❌ Erro ao importar modelos: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_schemas_validation():
    """Testa validação dos schemas Pydantic."""
    print("\n" + "=" * 60)
    print("Teste 5: Validação de Schemas")
    print("=" * 60)

    try:
        from app.schemas.analysis_job import AnalysisJobCreate

        # Testar validação de valor monetário válido
        print("\n1. Testando valor monetário válido:")
        job_create = AnalysisJobCreate(
            renda_mensal_declarada="2500.00", gasto_dividas_declarado="800,50"
        )
        print(f"   ✅ Renda: {job_create.renda_mensal_declarada}")
        print(f"   ✅ Gasto: {job_create.gasto_dividas_declarado}")

        # Testar validação de formato BR
        print("\n2. Testando formato brasileiro:")
        job_create2 = AnalysisJobCreate(
            renda_mensal_declarada="R$ 3.500,00",
        )
        print(f"   ✅ Renda (formato BR): {job_create2.renda_mensal_declarada}")

        # Testar validação de valor negativo (deve falhar)
        print("\n3. Testando valor negativo (esperado falhar):")
        try:
            job_create3 = AnalysisJobCreate(renda_mensal_declarada="-100.00")
            print("   ❌ Deveria ter falhado!")
            return False
        except Exception as e:
            print(f"   ✅ Rejeitou valor negativo: {str(e)[:50]}...")

        return True
    except Exception as e:
        print(f"\n❌ Erro nos testes de schema: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Executa todos os testes."""
    try:
        # Teste 1: Imports
        result1 = await test_api_imports()

        # Teste 2: Estrutura
        result2 = await test_api_structure()

        # Teste 3: OpenAPI
        result3 = await test_openapi_schema()

        # Teste 4: Modelos
        result4 = await test_database_models()

        # Teste 5: Schemas
        result5 = await test_schemas_validation()

        # Resultado final
        print("\n" + "=" * 60)
        all_passed = result1 and result2 and result3 and result4 and result5
        if all_passed:
            print("✅ Todos os testes dos API Endpoints passaram!")
        else:
            print("❌ Alguns testes falharam")
        print("=" * 60)

        return all_passed

    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
