# ==============================================
# Calculadora de Consignados - Backend Dockerfile
# ==============================================
# Multi-stage build para otimizar tamanho da imagem

# ==============================================
# Stage 1: Base Python Image
# ==============================================
FROM python:3.12-slim AS base

# Configurar timezone para São Paulo
ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials
    gcc \
    g++ \
    make \
    # PostgreSQL client
    libpq-dev \
    # Git (para alguns pacotes Python)
    git \
    # Curl para healthchecks
    curl \
    # Tesseract OCR (opcional)
    tesseract-ocr \
    tesseract-ocr-por \
    # MuPDF dependencies
    libmupdf-dev \
    mupdf-tools \
    # Limpar cache
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN useradd -m -u 1000 appuser

# Configurar diretório de trabalho
WORKDIR /app

# Configurar PATH para incluir .local/bin
ENV PATH="/home/appuser/.local/bin:${PATH}"

# ==============================================
# Stage 2: Dependencies
# ==============================================
FROM base AS dependencies

# Copiar arquivos de dependências
COPY pyproject.toml requirements.txt ./

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -e .

# ==============================================
# Stage 3: Development
# ==============================================
FROM dependencies AS development

# Instalar dependências de desenvolvimento
RUN pip install --no-cache-dir -e ".[dev]"

# Copiar código fonte
COPY --chown=appuser:appuser . .

# Mudar para usuário não-root
USER appuser

# Expor porta
EXPOSE 8000

# Comando padrão (desenvolvimento com reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ==============================================
# Stage 4: Production
# ==============================================
FROM dependencies AS production

# Instalar dependências de produção
RUN pip install --no-cache-dir -e ".[prod]"

# Copiar código fonte
COPY --chown=appuser:appuser . .

# Mudar para usuário não-root
USER appuser

# Expor porta
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando padrão (produção com Gunicorn)
CMD ["gunicorn", "app.main:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]
