## Project Summary & Scope
- This repo implements a PDF analysis pipeline (FastAPI + Celery) and a Next.js UI for uploading 1-3 PDFs and displaying 7 financial outputs in the UI (backend returns 9 total outputs, with 2 legacy).
- Core pipeline: PDF text extraction -> LLM routing -> LLM extraction -> deterministic Evidence Gate -> competencia selection -> consolidation -> compute engine -> API result.
- All monetary values are stored and computed as centavos (BIGINT) and formatted for display as BRL.
- Agents must always respond in Brazilian Portuguese (pt-BR) in all outputs and communications.

## Prerequisites & Environment Setup
### Required versions
- Docker 24+ and Docker Compose v2
- Node.js 20.9.0+ and npm 10+
- Python 3.11+

### Environment variables
- Copy the template and fill required secrets:
```bash
cp .env.example .env
```
- Required: `OPENAI_API_KEY`, `SECRET_KEY` (min 32 chars).
- Local defaults are defined in `.env.example` and `docker-compose.yml`.

### Quick start (Docker)
```bash
make setup
make up
make migrate
```

### Service URLs (local)
```text
Frontend: http://localhost:3000
Backend Swagger: http://localhost:8000/docs
MinIO Console: http://localhost:9001
```

### Local dev without Docker
Backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Build & Test Instructions
### Makefile shortcuts (recommended)
```bash
make up
make down
make migrate
make test
make lint-backend
make lint-frontend
make format-backend
make format-frontend
```

### Backend (pytest)
```bash
cd backend
pytest -v
pytest -v --cov
pytest -v -m unit
pytest -v -m integration
```
- Pytest markers: `unit`, `integration`, `slow`, `llm`.

### Frontend (Vitest)
```bash
cd frontend
npm run test
npm run test:ui
npm run test:coverage
npm run lint
npm run type-check
npm run format
```

### Docker production builds
```bash
cd backend
docker build --target production -t calculadora-backend:latest .

cd frontend
docker build --target production -t calculadora-frontend:latest .
```

## Key Code Style & Architecture Guidelines
### Backend (FastAPI + Celery)
- Pipeline modules live in `backend/app/services/` and must remain aligned with the PRD flow.
- `pdf_extraction.py` and `ocr_service.py`: native PDF extraction with quality score; OCR only if score < 0.6; persist `used_ocr` and metadata (pages, size, timing).
- `router.py`: return JSON with `docFamily`, `confidence`, `capabilities`, `competenciasDetectadas`, `evidence`; if confidence < 0.5, force `OTHER_UNKNOWN`; include at least 2 evidence snippets with page numbers.
- `extractors.py`: NEVER compute sums; extract values only; missing fields -> `null` + alert; consignado lines extracted individually with evidence.
- `evidence_gate.py`: re-parse evidence text deterministically; tolerance +/- 0.01; critical fields are `salario_bruto` and `salario_liquido` (failed validation -> `FAILED`); enforce invariants like bruto >= liquido and descontos >= 0.
- `consolidator.py`: apply source priority rules per field; record provenance; if same-priority values diverge > 1%, add alert.
- `compute_engine.py`: compute in centavos only. Formulas:
```text
descontos = bruto - liquido (DIFFERENCE)
divida_mensal = 90% do total_descontos
divida_mensal_reduzida = 25% da divida_mensal
consignado_mensal = sum(linhas_consignado)
divida_total = sum(valor_total_contrato)
divida_total_reduzida = 25% da divida_total_consignada
parcelas_restantes = sum(parcelas_restantes or total_parcelas - parcelas_pagas)
```
- Percentuais são calculados em centavos com truncamento: `(valor_cent * percent) // 100`.
- `POST /v1/analysis/jobs`: 1-3 PDFs, max 10MB each, 25MB total; inputs `renda_mensal_declarada` and `gasto_dividas_declarado` in BRL string format; return 201 with `jobId` UUID.
- `GET /v1/analysis/jobs/{jobId}` returns status and progress info.
- `GET /v1/analysis/jobs/{jobId}/result` returns 9 outputs; return 202 if not ready and 500 if failed; sanitize evidence text for PII and truncate alerts to 50 chars.
- DB schema lives in `backend/app/models/` and migrations in `backend/alembic/`. Always create Alembic migrations for schema changes.

### Frontend (Next.js App Router)
- Pages live in `frontend/src/app/`; shared UI in `frontend/src/components/ui/`.
- Keep API types in `frontend/src/types/api.ts` in sync with backend schemas and response fields.
- All money in the UI is in centavos; use `formatCurrency` for display and `parseCurrency` for user input.
- UI currently hides legacy metrics `consignado_mensal` and `parcelas_restantes_total` (still computed/persisted in backend).

### Shared domain rules
- Document families (Phase 1): `PAYROLL_SALARY_STATEMENT`, `INSS_HISTORICO_CREDITOS`, `INSS_EXTRATO_CONSIGNADO`, `OTHER_UNKNOWN` (the router code also defines `LOAN_CONTRACT_GENERIC`; keep downstream handling consistent if you use it).
- Capabilities: `PROVIDES_GROSS_NET_DEDUCTIONS`, `PROVIDES_CONSIGNADO_LINES`, `PROVIDES_LOAN_CONTRACTS`, `PROVIDES_COMPETENCIA_TABLE`.
- Competencia normalization: always `YYYY-MM`; select the most recent across documents; if missing, infer current month and add an alert.

## Project Structure & Navigation Hints
- `backend/app/` core API, services, models, schemas.
- `backend/app/services/` extraction pipeline modules.
- `backend/app/workers/` Celery app + tasks.
- `backend/alembic/` migrations and `init.sql`.
- `frontend/src/app/` Next.js routes (upload, job status, results).
- `frontend/src/types/` API typing helpers.
- `docs/` reserved for architecture docs (currently empty).
- `PRD-calculadora-consignados-v1.0.md` is the product blueprint; align behavior with its RF/RNF rules.
- Root `AGENTS.md` applies repo-wide; add nested `backend/AGENTS.md` or `frontend/AGENTS.md` if service-specific rules diverge, and the closest file in the tree takes precedence. citeturn0search0
- `AGENTS.md` is plain Markdown with no required schema; use headings that help agents execute tasks. citeturn0search0

## Common Pitfalls & Do/Don't Rules
- Do keep all monetary values in centavos (BIGINT); do not store floats in DB or compute with floats.
- Do not let LLM prompts perform arithmetic; calculations belong in deterministic services only.
- Do not change document family strings, capability enums, or API field names without updating both backend and frontend types.
- Do sanitize any evidence text exposed in API responses; do not log or store PII in logs.
- Do keep upload limits consistent across frontend + backend (1-3 PDFs, 10MB each, 25MB total).
- Do update tests when changing extraction logic, validation rules, or compute formulas.
- Para testes, sempre que reiniciar o celery-worker, limpar dados e arquivos gerados (DB + storage) para começar do zero.
- Sempre que houver qualquer modificação de código, reiniciar o celery-worker e limpar o DB + storage antes de testar.

## PR / Commit / Release Workflow
- Branch naming: `feature/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/`.
- Use Conventional Commits:
```text
<tipo>(escopo opcional): <descricao>
```
Examples:
```text
feat(extractor): add support for new INSS layout
fix(evidence-gate): handle negative values correctly
```
- Before PR: run `make lint-backend`, `make lint-frontend`, and `make test`.
- PRs should include: description, change type, testing steps, and checklist completion.

## Security, Compliance & Dependency Rules
- Never commit secrets; use `.env` and keep `OPENAI_API_KEY` and `SECRET_KEY` out of git.
- Logs must not include PII (CPF/NIT, account numbers, or full financial values).
- PDF retention is 30 days and audit retention is 90 days (configurable in `backend/app/core/config.py`).
- Rate limits default to 10 jobs per user per hour and 100 requests per IP per minute; keep changes in sync with config and docs.
- RAG storage (when enabled) must only use redacted text; no raw PII in embeddings.
- New dependencies must be justified and added via `backend/pyproject.toml` or `frontend/package.json` (update lockfiles).
