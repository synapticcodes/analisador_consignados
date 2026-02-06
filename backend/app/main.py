"""
Calculadora de Consignados - Main Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import check_db_connection, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.
    Executa setup na inicialização e cleanup no shutdown.
    """
    # Startup
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📦 Environment: {settings.environment}")
    print(f"🔧 Debug mode: {settings.debug}")

    # Verificar conexão com banco
    db_ok = await check_db_connection()
    if db_ok:
        print("✅ Database connection OK")
    else:
        print("⚠️  Database connection failed")

    yield

    # Shutdown
    print(f"🛑 Shutting down {settings.app_name}")
    await close_db()


# ==============================================
# FastAPI Application
# ==============================================
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para extração e cálculo de indicadores financeiros de PDFs",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# ==============================================
# Middlewares
# ==============================================

# CORS
dev_origin_regex = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=dev_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ==============================================
# Routes
# ==============================================

# API v1 Router
app.include_router(api_router, prefix="/v1")


@app.get("/", tags=["Root"])
async def root():
    """Health check endpoint."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "healthy",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint para load balancers.
    Verifica conectividade com serviços críticos.
    """
    # Verificar database
    db_healthy = await check_db_connection()

    health = {
        "status": "healthy" if db_healthy else "degraded",
        "environment": settings.environment,
        "version": settings.app_version,
        "checks": {
            "database": "ok" if db_healthy else "failed",
            # TODO: Adicionar checks de:
            # "redis": "ok",
            # "s3": "ok",
            # "qdrant": "ok",
        },
    }

    return health


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check para Kubernetes.
    Indica se a aplicação está pronta para receber tráfego.
    """
    return {
        "status": "ready",
        "message": "Application is ready to serve traffic",
    }


# ==============================================
# Exception Handlers
# ==============================================

# TODO: Adicionar exception handlers customizados:
# - ValidationError
# - HTTPException
# - DatabaseError
# - LLMError
# - etc.

# ==============================================
# Events (Deprecated in FastAPI 0.128+, use lifespan instead)
# ==============================================

# Mantido para compatibilidade, mas preferir usar lifespan context manager
