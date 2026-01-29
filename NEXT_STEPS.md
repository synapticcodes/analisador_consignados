# 📋 Próximos Passos - Calculadora de Consignados

Este documento lista os próximos passos para implementar as funcionalidades principais do sistema.

## ✅ Concluído

- [x] Estrutura de pastas completa
- [x] Configuração de ambiente (Docker Compose)
- [x] Backend FastAPI com configurações
- [x] Frontend Next.js com Tailwind CSS
- [x] Schema de banco de dados (DDL)
- [x] Dockerfiles otimizados
- [x] Configurações de desenvolvimento
- [x] Documentação inicial
- [x] Database Models (SQLAlchemy) - User, AnalysisJob, UploadedFile, DocumentExtraction, LoanContract, PayrollMonth, FinalResult
- [x] Database.py com async engine configurado
- [x] Schemas Pydantic para validação
- [x] PDF Extraction Service (PyMuPDF + OCR fallback) - Testado ✅

## 🚧 Fase 1: MVP (8-10 semanas)

### Backend - Semana 1-2

- [x] **Database Models (SQLAlchemy)**
  - [x] Criar models em `backend/app/models/`
  - [x] User, AnalysisJob, UploadedFile, DocumentExtraction
  - [x] LoanContract, PayrollMonth, FinalResult
  - [x] Configurar database.py com async engine

- [ ] **Infraestrutura Base**
  - [ ] Configurar S3/MinIO client
  - [ ] Configurar Redis client
  - [ ] Configurar Qdrant client
  - [ ] Configurar OpenAI client

### Backend - Semana 2-3

- [x] **PDF Extraction Service**
  - [x] Implementar extração com PyMuPDF
  - [x] Implementar fallback OCR (AWS Textract)
  - [x] Calcular score de qualidade
  - [x] Arquivo: `backend/app/services/pdf_extraction.py`

### Backend - Semana 3-4

- [x] **Router LLM (GPT-4)**
  - [x] Criar prompt Router (baseado no PRD seção 10.1)
  - [x] Implementar classificação de documentos
  - [x] Retornar família + capabilities + evidências
  - [x] Arquivo: `backend/app/services/router.py` - Testado ✅

### Backend - Semana 4-5

- [x] **Extractors LLM**
  - [x] Payment Extractor (folha/INSS - seção 10.2)
  - [x] Loan Extractor (contratos - seção 10.3)
  - [x] Schemas Pydantic para respostas
  - [x] Arquivo: `backend/app/services/extractors.py` - Testado ✅

### Backend - Semana 5-6

- [x] **Evidence Gate (Validação Determinística)**
  - [x] Regex para parsing de valores BR
  - [x] Re-parsing de evidências
  - [x] Validação de invariantes matemáticos
  - [x] Arquivo: `backend/app/services/evidence_gate.py` - Testado ✅

### Backend - Semana 6-7

- [x] **Consolidator & Compute Engine**
  - [x] Seleção de competência alvo
  - [x] Resolução de conflitos (prioridades)
  - [x] Cálculos em centavos (BIGINT)
  - [x] Arquivo: `backend/app/services/consolidator.py` - Testado ✅
  - [x] Arquivo: `backend/app/services/compute_engine.py` - Testado ✅

### Backend - Semana 7-8

- [x] **API Endpoints (FastAPI)**
  - [x] POST `/v1/analysis/jobs` - Upload PDFs
  - [x] GET `/v1/analysis/jobs/{jobId}` - Status
  - [x] GET `/v1/analysis/jobs/{jobId}/result` - Resultado
  - [x] Arquivo: `backend/app/api/v1/analysis.py` - Testado ✅

- [x] **Celery Tasks**
  - [x] Configurar Celery app
  - [x] Task: process_job (orquestra pipeline)
  - [x] Arquivo: `backend/app/workers/tasks.py` - Testado ✅

### Frontend - Semana 8-9

- [x] **Página de Upload**
  - [x] Componente de drag-and-drop (react-dropzone)
  - [x] Validação de arquivos (tamanho, formato)
  - [x] Preview de thumbnails
  - [x] Formulário de dados declarados
  - [x] Arquivo: `frontend/src/app/upload/page.tsx` - Implementado ✅

- [x] **Página de Progresso**
  - [x] Polling de status
  - [x] Barra de progresso
  - [x] Indicador de etapas
  - [x] Arquivo: `frontend/src/app/jobs/[id]/page.tsx` - Implementado ✅

- [x] **Página de Resultados**
  - [x] Cards dos 6 outputs
  - [x] Modal de evidências
  - [x] Lista de alertas
  - [x] Arquivo: `frontend/src/app/jobs/[id]/result/page.tsx` - Implementado ✅

### Testing - Semana 9

- [ ] **Testes Backend**
  - [ ] Testes unitários (pytest)
  - [ ] Testes de Evidence Gate
  - [ ] Testes de Consolidator
  - [ ] Mocks para LLM

- [ ] **Testes Frontend**
  - [ ] Testes de componentes (Vitest)
  - [ ] Testes de integração

### Deploy - Semana 10

- [ ] **Staging Deploy**
  - [ ] Configurar ambiente de staging
  - [ ] Deploy via Docker Compose
  - [ ] Testes end-to-end

## 📊 Fase 2: RAG e Observabilidade (4-6 semanas)

### Backend - Semana 11-12

- [ ] **RAG (Qdrant)**
  - [ ] Pipeline de redaction (PII removal)
  - [ ] Chunking de texto
  - [ ] Geração de embeddings
  - [ ] Storage em Qdrant
  - [ ] Arquivo: `backend/app/services/rag.py`

### Backend - Semana 12-13

- [ ] **Repair Agent**
  - [ ] Prompt Repair Agent (seção 10.4)
  - [ ] Busca de casos similares
  - [ ] Proposta de melhorias
  - [ ] Arquivo: `backend/app/services/repair_agent.py`

### Observability - Semana 14-15

- [ ] **OpenTelemetry**
  - [ ] Configurar traces
  - [ ] Instrumentar endpoints
  - [ ] Exportar para Jaeger/Tempo

- [ ] **Prometheus + Grafana**
  - [ ] Métricas de negócio
  - [ ] Dashboards operacionais
  - [ ] Alertas

### Testing - Semana 15-16

- [ ] **Golden Tests**
  - [ ] Coletar 20+ PDFs representativos
  - [ ] Criar expected outputs
  - [ ] Suite de testes anti-regressão
  - [ ] Integrar no CI/CD

## 🚀 Fase 3: Auto-aprimoramento (6-8 semanas)

- [ ] **Promote Engine**
  - [ ] Validação automática de propostas
  - [ ] Testes anti-regressão
  - [ ] Rollback automático

- [ ] **Expansão de Famílias**
  - [ ] Suporte a novos layouts
  - [ ] BANK_STATEMENT

- [ ] **Otimizações**
  - [ ] Cache de embeddings
  - [ ] Redução de custo LLM
  - [ ] Performance tuning

---

## 🔧 Quick Commands

```bash
# Setup inicial
make setup

# Subir serviços
make up

# Ver logs
make logs

# Rodar testes
make test

# Ver este arquivo
cat NEXT_STEPS.md
```

## 📚 Referências

- **PRD Completo**: [PRD-calculadora-consignados-v1.0.md](PRD-calculadora-consignados-v1.0.md)
- **API Docs**: http://localhost:8000/docs
- **Prompts LLM**: PRD seção 10 (Anexo C)

---

**Última atualização:** 2026-01-28
