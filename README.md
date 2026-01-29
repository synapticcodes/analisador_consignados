# 🧮 Calculadora de Consignados

[![Next.js](https://img.shields.io/badge/Next.js-16.1.5-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128.0-009688)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-336791)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Sistema de **extração inteligente e cálculo de indicadores financeiros** a partir de documentos PDF (contracheques, extratos INSS, extratos de empréstimo consignado) com **confiabilidade matemática 100%**.

## 🎯 Visão Geral

A Calculadora de Consignados combina:
- **🤖 LLM (GPT-4)** para extração flexível de milhares de layouts diferentes
- **🔒 Validação determinística** para garantir precisão matemática absoluta
- **📊 6 Indicadores Financeiros**: Salário Bruto, Líquido, Descontos, Consignado Mensal, Dívida Total, Parcelas Restantes

### Principais Características

- ✅ Upload de até **3 PDFs simultâneos**
- ✅ Processamento assíncrono com progresso em tempo real
- ✅ **100% precisão matemática** (cálculos em centavos BIGINT)
- ✅ Evidências completas (rastreabilidade de cada valor extraído)
- ✅ Suporte a múltiplos tipos de documentos (folhas de pagamento, INSS, extratos)
- ✅ Tempo médio de processamento: **< 45 segundos** (P90)

---

## 🚀 Quick Start (< 5 minutos)

### Pré-requisitos

**Obrigatórios:**
- [Docker 24+](https://docs.docker.com/get-docker/) e Docker Compose v2
- [Node.js 20.9.0+](https://nodejs.org/) (LTS)
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)

**Verificar versões:**
```bash
node --version   # v20.9.0+
python --version # 3.11.0+
docker --version # 24.0.0+
```

### Setup Rápido

```bash
# 1. Clonar repositório
git clone https://github.com/seu-org/calculadora-consignados.git
cd calculadora-consignados

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Edite .env com suas chaves (OPENAI_API_KEY obrigatório)

# 3. Subir toda a infraestrutura
docker-compose up -d

# 4. Aguardar serviços ficarem prontos (health checks)
docker-compose ps

# 5. Rodar migrations do banco
docker-compose exec backend alembic upgrade head

# 6. Acessar aplicação
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs (Swagger)
# MinIO Console: http://localhost:9001
```

### Credenciais Padrão (Desenvolvimento)

| Serviço | Usuário | Senha | URL |
|---------|---------|-------|-----|
| **MinIO Console** | `minioadmin` | `minioadmin123` | http://localhost:9001 |
| **PostgreSQL** | `postgres` | `postgres_dev_password` | localhost:5432 |
| **Redis** | - | `redis_dev_password` | localhost:6379 |

> ⚠️ **IMPORTANTE**: Troque todas as senhas em produção!

---

## 📦 Stack Tecnológica (2026)

### Frontend
- **Framework**: [Next.js 16.1.5](https://nextjs.org/) (App Router)
- **UI**: [React 19.2](https://react.dev/) + [Tailwind CSS v4](https://tailwindcss.com/)
- **Type Safety**: TypeScript 5.7+
- **Testes**: Vitest + Testing Library

### Backend
- **Framework**: [FastAPI 0.128.0](https://fastapi.tiangolo.com/) (Python 3.11+)
- **ORM**: SQLAlchemy 2.0 (Async)
- **Validação**: Pydantic v2
- **Task Queue**: Celery 5.4 + Redis
- **Testes**: pytest 9.0+

### Infraestrutura
- **Database**: PostgreSQL 18 (AIO, temporal constraints)
- **Cache/Queue**: Redis 7
- **Vector DB**: Qdrant 1.12+ (para RAG - Fase 2)
- **Storage**: MinIO (S3-compatible)
- **LLM**: OpenAI GPT-4 / GPT-4o

### Observabilidade
- **Logs**: JSON estruturado + stdout
- **Traces**: OpenTelemetry (Fase 2)
- **Metrics**: Prometheus (Fase 2)

---

## 🏗️ Estrutura do Projeto

```
calculadora-consignados/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/               # Endpoints REST
│   │   ├── core/              # Configurações, segurança
│   │   ├── models/            # SQLAlchemy models
│   │   ├── services/          # Lógica de negócio
│   │   ├── workers/           # Celery tasks
│   │   └── main.py            # Entry point
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Testes pytest
│   ├── pyproject.toml         # Dependências Python
│   └── Dockerfile
│
├── frontend/                   # Next.js Frontend
│   ├── src/
│   │   ├── app/               # Next.js App Router
│   │   ├── components/        # Componentes React
│   │   ├── lib/               # Utilities
│   │   └── types/             # TypeScript types
│   ├── public/                # Assets estáticos
│   ├── package.json           # Dependências Node
│   ├── tailwind.config.ts     # Tailwind CSS config
│   └── Dockerfile
│
├── docs/                       # Documentação
├── docker-compose.yml          # Orquestração local
├── .env.example                # Template de variáveis
└── README.md
```

---

## 🛠️ Desenvolvimento Local

### Backend (FastAPI)

```bash
cd backend

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependências
pip install -e ".[dev]"

# Rodar servidor (com reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Rodar testes
pytest -v --cov

# Linting e formatação
ruff check .
black .
```

**API Documentation**: http://localhost:8000/docs

### Frontend (Next.js)

```bash
cd frontend

# Instalar dependências
npm install

# Rodar dev server (com hot reload)
npm run dev

# Build de produção
npm run build

# Rodar testes
npm run test

# Formatação
npm run format
```

**Frontend URL**: http://localhost:3000

### Celery Worker (Background Tasks)

```bash
cd backend
source venv/bin/activate

# Rodar worker
celery -A app.workers.celery_app worker --loglevel=info --concurrency=2
```

---

## 🗄️ Banco de Dados

### Migrations (Alembic)

```bash
# Criar nova migration
docker-compose exec backend alembic revision --autogenerate -m "descrição"

# Aplicar migrations
docker-compose exec backend alembic upgrade head

# Reverter migration
docker-compose exec backend alembic downgrade -1

# Ver histórico
docker-compose exec backend alembic history
```

### Schema Principal

- **users**: Usuários do sistema
- **analysis_jobs**: Jobs de análise de PDFs
- **uploaded_files**: Arquivos PDF enviados
- **document_extractions**: Extrações de dados dos documentos
- **loan_contracts**: Contratos de empréstimo extraídos
- **payroll_months**: Dados de folha de pagamento por competência
- **final_results**: Resultados consolidados finais (6 outputs)

Ver DDL completo: [`backend/alembic/init.sql`](backend/alembic/init.sql)

---

## 📝 Variáveis de Ambiente

### Obrigatórias

```bash
# OpenAI (OBRIGATÓRIO)
OPENAI_API_KEY=sk-proj-your-key-here

# Segurança
SECRET_KEY=change_this_secret_key_min_32_chars
```

### Opcionais (com defaults)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres_dev_password@postgres:5432/calculadora_consignados

# Redis
REDIS_URL=redis://:redis_dev_password@redis:6379/0

# MinIO/S3
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin123

# AWS Textract (OCR opcional)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
```

Ver todas as variáveis: [`.env.example`](.env.example)

---

## 🧪 Testes

### Backend (pytest)

```bash
cd backend

# Rodar todos os testes
pytest -v

# Com cobertura
pytest -v --cov --cov-report=html

# Apenas testes unitários
pytest -v -m unit

# Apenas testes de integração
pytest -v -m integration

# Ver relatório de cobertura
open htmlcov/index.html
```

### Frontend (Vitest)

```bash
cd frontend

# Rodar testes
npm run test

# Com UI interativa
npm run test:ui

# Cobertura
npm run test:coverage
```

---

## 🚢 Deploy

### Build de Produção

```bash
# Backend
cd backend
docker build --target production -t calculadora-backend:latest .

# Frontend
cd frontend
docker build --target production -t calculadora-frontend:latest .
```

### Deploy com Docker Compose (Produção)

1. Edite `.env` com credenciais de produção
2. Configure `ENVIRONMENT=production` e `DEBUG=false`
3. Execute:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Checklist de Produção

- [ ] Trocar todas as senhas padrão
- [ ] Configurar HTTPS/TLS
- [ ] Configurar domínio e DNS
- [ ] Configurar backups automáticos (PostgreSQL)
- [ ] Configurar monitoramento (Prometheus + Grafana)
- [ ] Configurar error tracking (Sentry)
- [ ] Configurar rate limiting adequado
- [ ] Revisar políticas de retenção de dados
- [ ] Configurar CI/CD pipeline
- [ ] Executar penetration testing

---

## 📊 Métricas de Sucesso (KPIs)

| KPI | Meta Fase 1 (MVP) | Meta Fase 3 |
|-----|-------------------|-------------|
| **Taxa de Extração Bem-Sucedida** | ≥70% | ≥95% |
| **Precisão de Valores** | ≥90% | ≥97% |
| **Tempo de Processamento (P90)** | <45s | <20s |
| **Confiabilidade Matemática** | 100% | 100% |
| **Cobertura de Documentos** | ≥70% | ≥95% |

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Code Style

- **Backend**: Black + Ruff (linha 100 chars)
- **Frontend**: Prettier + ESLint
- **Commits**: Conventional Commits

---

## 📖 Documentação Adicional

- [PRD Completo](PRD-calculadora-consignados-v1.0.md)
- [Arquitetura Técnica](docs/architecture.md) (TODO)
- [API Documentation](http://localhost:8000/docs) (Swagger)
- [Guia de Contribuição](CONTRIBUTING.md) (TODO)

---

## 🐛 Troubleshooting

### Problema: Serviços não sobem

```bash
# Verificar logs
docker-compose logs -f

# Limpar volumes e recriar
docker-compose down -v
docker-compose up -d --build
```

### Problema: Migrations falhando

```bash
# Resetar banco (ATENÇÃO: perde dados!)
docker-compose down -v postgres
docker-compose up -d postgres
docker-compose exec backend alembic upgrade head
```

### Problema: Frontend não conecta com backend

Verifique se `NEXT_PUBLIC_API_URL` em `.env` aponta para o backend correto.

---

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 🙏 Agradecimentos

- FastAPI por um framework Python excepcional
- Next.js/Vercel pela melhor experiência de desenvolvimento React
- OpenAI pela capacidade de LLM
- Comunidade open source 🎉

---

## 📞 Contato e Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-org/calculadora-consignados/issues)
- **Email**: suporte@seudominio.com
- **Documentação**: [Wiki](https://github.com/seu-org/calculadora-consignados/wiki)

---

<div align="center">

**Feito com ❤️ pela equipe Calculadora de Consignados**

[⬆ Voltar ao topo](#-calculadora-de-consignados)

</div>
