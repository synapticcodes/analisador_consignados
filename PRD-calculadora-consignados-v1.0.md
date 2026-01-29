# PRD: Calculadora de Consignados com Extração Inteligente de PDFs

## Sumário Executivo

A Calculadora de Consignados é uma solução automatizada para extração e cálculo de indicadores financeiros a partir de documentos PDF (contracheques, extratos INSS, extratos de empréstimo consignado). O sistema permite que usuários façam upload de até 3 PDFs simultaneamente e, através de extração inteligente baseada em LLM (GPT-5.2) combinada com validação determinística, obtém 6 indicadores financeiros essenciais: salário bruto, salário líquido, total de descontos, consignado mensal, dívida total consignada e parcelas restantes.

O diferencial do produto está na combinação de **confiabilidade matemática** (todos os cálculos são determinísticos em código) com **flexibilidade de extração** (LLM interpreta milhares de layouts diferentes de PDF sem necessidade de mapeamento manual). O sistema garante auditabilidade total através de evidências (trechos dos PDFs que sustentam cada valor) e implementa auto-aprimoramento contínuo através da "Camada C", que propõe melhorias validadas por testes anti-regressão.

O produto visa atender instituições financeiras, fintechs de crédito consignado, e consultorias que precisam analisar capacidade de crédito de beneficiários INSS e trabalhadores CLT de forma rápida, precisa e escalável.

---

## 🚀 Quick Start Guide (Stack 2026)

### Pré-requisitos

**Obrigatórios:**
- Node.js 20.9.0+ (LTS)
- Python 3.11+ (recomendado 3.12)
- Docker 24+ e Docker Compose v2
- Git

**Verificar versões:**
```bash
node --version   # v20.9.0+
python --version # 3.11.0+
docker --version # 24.0.0+
```

### Setup Rápido (< 5 minutos)

```bash
# 1. Clonar repositório
git clone https://github.com/seu-org/calculadora-consignados.git
cd calculadora-consignados

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas chaves (OPENAI_API_KEY obrigatório)

# 3. Subir toda a infraestrutura (PostgreSQL 18, Redis, Qdrant, MinIO)
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

### Desenvolvimento Local

**Backend (FastAPI 0.128 + Python 3.11):**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

**Frontend (Next.js 16 + React 19):**
```bash
cd frontend
npm install
npm run dev
```

**Testes:**
```bash
# Backend (pytest 9.0)
cd backend
pytest -v --cov

# Frontend (Vitest)
cd frontend
npm run test
```

### Stack Completo (versões atualizadas 2026)

| Componente | Versão | Porta | Documentação |
|------------|--------|-------|--------------|
| **Frontend** | Next.js 16.1+ | 3000 | [Next.js Docs](https://nextjs.org/docs) |
| **Backend** | FastAPI 0.128+ | 8000 | Ver `/docs` |
| **Database** | PostgreSQL 18 | 5432 | [PG 18 Release](https://www.postgresql.org/docs/18/) |
| **Cache/Queue** | Redis 7 | 6379 | - |
| **Vector DB** | Qdrant 1.12+ | 6333/6334 | [Qdrant Docs](https://qdrant.tech/documentation/) |
| **Storage** | MinIO (S3) | 9000/9001 | - |

### Configurações Prontas

Todas as configurações de produção estão no **Anexo E** deste PRD:
- ✅ `package.json` (Node 20 + Next.js 16 + React 19 + Tailwind v4)
- ✅ `pyproject.toml` (Python 3.11 + FastAPI 0.128 + Pydantic v2 + pytest 9.0)
- ✅ `docker-compose.yml` (stack completo)
- ✅ Dockerfiles otimizados
- ✅ DDL PostgreSQL 18 com temporal constraints
- ✅ `.env.example` completo

### Próximos Passos

1. Revisar **RNF-010** (Requisitos de Runtime) para breaking changes
2. Consultar **Anexo E** para configurações detalhadas
3. Ler seção de **Arquitetura Técnica** (diagramas)
4. Revisar **Cronograma Fase 1** (8-10 semanas)

---

## Problema

### Contexto

A análise de crédito consignado no Brasil envolve processar dezenas de tipos diferentes de documentos: contracheques de diferentes empresas, históricos de crédito do INSS, extratos de empréstimos de diversos bancos. Cada órgão, empresa ou instituição financeira utiliza layouts, nomenclaturas e estruturas de dados completamente diferentes.

Atualmente, esse processo é feito de três formas:
1. **Manualmente**: analistas leem PDFs e digitam valores em planilhas (lento, sujeito a erro humano)
2. **OCR + regex fixos**: sistemas tentam extrair campos com regras fixas (quebram quando o layout muda)
3. **LLMs sem validação**: sistemas modernos usam IA mas sem garantia de precisão matemática (risco de alucinação em valores financeiros)

### Problema Principal

**Como extrair e calcular com 100% de confiabilidade matemática indicadores financeiros de documentos PDF com layouts infinitamente variáveis, sem exigir mapeamento manual de cada tipo de documento?**

Subproblemas:
- Impossibilidade de mapear milhares de layouts de documentos manualmente
- Risco de erro de cálculo em sistemas que delegam matemática para LLM
- Falta de rastreabilidade: valores extraídos sem evidência clara de onde vieram
- Inconsistências entre múltiplos documentos do mesmo cliente
- Impossibilidade de melhorar o sistema sem retrabalho manual

### Impacto do Problema

**Quantitativo (estimado para instituições financeiras de médio porte):**
- Tempo médio de análise manual: **15-30 minutos por cliente**
- Taxa de erro em digitação manual: **3-5% dos valores**
- Custo de retrabalho por erro: **R$ 150-500 por caso**
- PDFs rejeitados por sistemas baseados em regex: **30-40%** (exigem análise manual)

**Qualitativo:**
- Experiência do cliente degradada por lentidão no processo
- Risco de compliance (erros em cálculo de margem consignável)
- Impossibilidade de escalar operação sem crescimento proporcional de equipe

---

## Solução Proposta

### Visão Geral

O sistema implementa uma **arquitetura híbrida de 3 camadas**:

**Camada A - Extração (LLM):** GPT-5.2 analisa o PDF e classifica o tipo de documento (família), identifica campos relevantes e extrai valores com evidências (trechos exatos do texto + página).

**Camada B - Validação e Cálculo (Determinística):**
- Evidence Gate valida que cada valor extraído tem evidência localizável e parseável
- Consolidador resolve conflitos entre múltiplos documentos priorizando fontes confiáveis
- Compute Engine executa todos os cálculos em código (centavos como BIGINT) garantindo precisão matemática

**Camada C - Auto-aprimoramento (Semi-automática):**
- Sistema armazena casos anteriores em RAG (embeddings)
- Repair Agent (GPT-5.2) propõe melhorias quando detecta falhas
- Melhorias só são promovidas se passarem em testes anti-regressão automáticos

### Objetivos e Métricas de Sucesso

| Objetivo | Métrica | Meta Fase 1 (MVP) | Meta Fase 3 (Maduro) |
|----------|---------|-------------------|----------------------|
| Precisão de extração | % de campos extraídos corretamente vs. validação manual | ≥ 90% | ≥ 97% |
| Cobertura de documentos | % de PDFs processados com sucesso (≥4 dos 6 outputs) | ≥ 70% | ≥ 95% |
| Confiabilidade matemática | % de cálculos corretos (zero tolerância a erro) | 100% | 100% |
| Velocidade de processamento | Tempo médio para processar 3 PDFs | < 45 segundos | < 20 segundos |
| Rastreabilidade | % de valores com evidência válida | 100% | 100% |
| Redução de custo operacional | Redução de tempo vs. análise manual | 80% | 95% |

---

## Requisitos Funcionais

### RF-001: Upload de PDFs
**Prioridade:** P0
**Estimativa:** 3 pontos

**Descrição:**
Sistema deve permitir upload simultâneo de 1 a 3 arquivos PDF através de interface web drag-and-drop.

**Critérios de Aceite:**
- [ ] CA-001: Aceita arquivos com extensão .pdf
- [ ] CA-002: Valida tamanho máximo de 10MB por arquivo
- [ ] CA-003: Valida total máximo de 25MB para os 3 arquivos combinados
- [ ] CA-004: Rejeita arquivos corrompidos ou protegidos por senha antes do processamento
- [ ] CA-005: Exibe preview visual (thumbnail da primeira página) após upload
- [ ] CA-006: Permite remover arquivo individual antes do envio final

**Regras de Negócio:**
- RN-001: Mínimo 1 PDF, máximo 3 PDFs por job
- RN-002: PDFs são armazenados com criptografia (S3 SSE ou equivalente)
- RN-003: Nome original do arquivo é preservado para auditoria

**Fluxo Principal:**
1. Usuário acessa tela de upload
2. Usuário arrasta arquivos ou clica para selecionar
3. Sistema valida cada arquivo (tamanho, formato, integridade)
4. Sistema exibe lista de arquivos aceitos com preview
5. Usuário confirma e avança para formulário

**Fluxos de Exceção:**
- FE-001: Arquivo > 10MB → Exibe "Arquivo muito grande. Máximo: 10MB"
- FE-002: Mais de 3 arquivos → Desabilita upload adicional
- FE-003: PDF corrompido → Exibe "Arquivo corrompido ou protegido por senha"

---

### RF-002: Entrada de Dados Declarados
**Prioridade:** P0
**Estimativa:** 2 pontos

**Descrição:**
Sistema deve capturar renda mensal declarada e gasto mensal com dívidas declarados pelo usuário no mesmo formulário de upload.

**Critérios de Aceite:**
- [ ] CA-001: Campo "Renda Mensal Declarada" aceita valores em formato BRL (ex: R$ 2.500,00)
- [ ] CA-002: Campo "Gasto Mensal com Dívidas Declarado" aceita valores em formato BRL
- [ ] CA-003: Campos aceitam entrada com máscara de moeda (formatação automática)
- [ ] CA-004: Validação de valores entre R$ 0,01 e R$ 999.999,99
- [ ] CA-005: Ambos os campos são opcionais (podem ficar em branco)

**Regras de Negócio:**
- RN-001: Valores declarados NUNCA substituem valores extraídos, exceto como fallback explícito
- RN-002: Sistema armazena valores declarados em centavos (BIGINT)
- RN-003: Se valor extraído divergir >20% do declarado, gera alerta

**Fluxo Principal:**
1. Usuário insere renda mensal declarada
2. Sistema formata automaticamente (ex: digita "2500" → exibe "R$ 2.500,00")
3. Usuário insere gasto mensal declarado
4. Sistema valida e armazena valores

**Fluxos de Exceção:**
- FE-001: Valor negativo → Exibe "Valor deve ser positivo"
- FE-002: Valor > R$ 999.999,99 → Exibe "Valor máximo excedido"

---

### RF-003: Processamento Assíncrono de Job
**Prioridade:** P0
**Estimativa:** 8 pontos

**Descrição:**
Sistema deve criar job assíncrono para processar PDFs através de pipeline de extração, validação e consolidação.

**Critérios de Aceite:**
- [ ] CA-001: Ao submeter formulário, sistema cria job com UUID único
- [ ] CA-002: Job retorna imediatamente com status "PENDING"
- [ ] CA-003: Pipeline executa etapas na ordem: Extract → Route → Parse → Gate → Consolidate → Compute
- [ ] CA-004: Cada etapa atualiza status do job (progress %)
- [ ] CA-005: Job transiciona para "SUCCEEDED" ou "FAILED" ao final
- [ ] CA-006: Falhas são categorizadas (error_code) sem expor PII

**Regras de Negócio:**
- RN-001: Pipeline usa Temporal.io ou Celery para orquestração
- RN-002: Timeout total do job: 5 minutos
- RN-003: Retry automático em falhas transientes (max 3 tentativas)
- RN-004: PDFs são deletados após 30 dias (configurável)

**Fluxo Principal:**
1. Sistema recebe upload + dados declarados
2. Cria registro em `analysis_jobs` (status=PENDING)
3. Cria registros em `uploaded_files` com S3 URLs
4. Enfileira job no pipeline
5. Worker executa pipeline (etapas detalhadas em RF-004 a RF-010)
6. Atualiza status final e resultados

**Fluxos de Exceção:**
- FE-001: Timeout após 5 min → status=FAILED, error_code="TIMEOUT"
- FE-002: Todos os PDFs falharam extração → status=FAILED, error_code="EXTRACTION_FAILED"
- FE-003: Erro inesperado → status=FAILED, log estruturado para debugging

---

### RF-004: Extração de Texto e Layout
**Prioridade:** P0
**Estimativa:** 5 pontos

**Descrição:**
Sistema deve extrair texto nativo do PDF com preservação de layout (posições, tabelas) e acionar OCR como fallback quando texto nativo for insuficiente.

**Critérios de Aceite:**
- [ ] CA-001: Usa PyMuPDF ou pdfplumber para extração de texto nativo
- [ ] CA-002: Preserva estrutura de tabelas quando detectadas
- [ ] CA-003: Detecta qualidade de extração (score 0-1 baseado em % de caracteres válidos)
- [ ] CA-004: Se score < 0.6, aciona OCR (AWS Textract ou Google Document AI)
- [ ] CA-005: Armazena flag `used_ocr` em `document_extractions`

**Regras de Negócio:**
- RN-001: OCR só é acionado quando estritamente necessário (custo)
- RN-002: Texto extraído é armazenado com coordenadas de página quando possível
- RN-003: Metadados incluem: n_pages, file_size, extraction_time_ms

**Fluxo Principal:**
1. Worker baixa PDF do S3
2. Executa extração de texto nativo página por página
3. Calcula score de qualidade
4. Se score >= 0.6, prossegue com texto nativo
5. Se score < 0.6, aciona OCR para páginas problemáticas
6. Persiste texto + metadados

**Fluxos de Exceção:**
- FE-001: PDF corrompido → Falha com error_code="CORRUPT_FILE"
- FE-002: OCR timeout → Tenta com texto parcial, marca alerta

---

### RF-005: Roteamento de Documento (Router GPT-5.2)
**Prioridade:** P0
**Estimativa:** 8 pontos

**Descrição:**
Sistema deve classificar cada PDF em uma "família" (ex: PAYROLL_SALARY_STATEMENT, INSS_HISTORICO_CREDITOS, INSS_EXTRATO_CONSIGNADO) e identificar suas "capabilities" (dados que pode fornecer).

**Critérios de Aceite:**
- [ ] CA-001: Router usa prompt estruturado (seção 10.1 do blueprint)
- [ ] CA-002: Retorna JSON com: docFamily, confidence (0-1), capabilities[], competenciasDetectadas[], evidence[]
- [ ] CA-003: Evidence contém mínimo 2 trechos de texto com página
- [ ] CA-004: Se confidence < 0.5, marca docFamily="OTHER_UNKNOWN"
- [ ] CA-005: Armazena resultado completo em `document_extractions.extracted_json`

**Regras de Negócio:**
- RN-001: Famílias suportadas (Fase 1): PAYROLL_SALARY_STATEMENT, INSS_HISTORICO_CREDITOS, INSS_EXTRATO_CONSIGNADO, OTHER_UNKNOWN
- RN-002: Capabilities suportadas: PROVIDES_GROSS_NET_DEDUCTIONS, PROVIDES_CONSIGNADO_LINES, PROVIDES_LOAN_CONTRACTS, PROVIDES_COMPETENCIA_TABLE
- RN-003: Router nunca executa cálculos, apenas classifica

**Fluxo Principal:**
1. Recebe texto extraído + metadados
2. Monta prompt Router com snippet de texto (primeiras 3000 chars + metadados)
3. Chama GPT-5.2 com temperature=0.1
4. Parseia JSON de resposta
5. Valida schema de resposta
6. Persiste em `document_extractions`

**Fluxos de Exceção:**
- FE-001: GPT retorna JSON inválido → Retry 1x, se falhar marca confidence=0
- FE-002: Timeout (>30s) → Marca OTHER_UNKNOWN com alerta

---

### RF-006: Extração Estruturada de Dados (Extractors GPT-5.2)
**Prioridade:** P0
**Estimativa:** 13 pontos

**Descrição:**
Sistema deve extrair valores estruturados (salários, descontos, contratos) de cada documento usando extractor específico por família, com evidências obrigatórias.

**Critérios de Aceite:**
- [ ] CA-001: Usa extractor específico baseado em `docFamily` (Payment Extractor para folha/INSS, Loan Extractor para contratos)
- [ ] CA-002: Retorna JSON estruturado com schema específico (seções 10.2 e 10.3)
- [ ] CA-003: Cada valor extraído inclui: value, currency, method, evidence {page, text}
- [ ] CA-004: Se campo não existir, retorna value=null + alerta explicativo
- [ ] CA-005: Extractor NUNCA executa somas/cálculos, apenas extrai valores individuais
- [ ] CA-006: Linhas de consignado são extraídas individualmente (não somadas)

**Regras de Negócio:**
- RN-001: Payment Extractor identifica: bruto, líquido, descontos total, linhas de consignado por competência
- RN-002: Loan Extractor identifica: contratos com parcela mensal, total parcelas, parcelas pagas/restantes, valor total contrato
- RN-003: Rubricas de consignado conhecidas (expansível): 216, 217, 268, "CONSIGNACAO", "EMPRESTIMO"
- RN-004: Evidence.text deve conter o valor exato ou trecho inequívoco

**Fluxo Principal:**
1. Recebe texto completo + docFamily + capabilities
2. Seleciona template de prompt adequado
3. Chama GPT-5.2 com temperature=0
4. Parseia resposta JSON
5. Valida schema de resposta
6. Persiste em `document_extractions.extracted_json`

**Fluxos de Exceção:**
- FE-001: JSON inválido → Retry 1x, se falhar marca gate_status=FAILED
- FE-002: Evidence vazia para campo crítico → Marca value=null + alerta

---

### RF-007: Validação Determinística (Evidence Gate)
**Prioridade:** P0
**Estimativa:** 8 pontos

**Descrição:**
Sistema deve validar cada valor extraído através de re-parsing do trecho de evidência, garantindo que LLM não alucininou valores.

**Critérios de Aceite:**
- [ ] CA-001: Para cada campo com value != null, re-parseia evidence.text usando regex determinístico
- [ ] CA-002: Normaliza valores BR (R$ 1.334,36 → 1334.36) com regras fixas
- [ ] CA-003: Compara valor extraído vs. re-parseado com tolerância de ±0.01 (formatação)
- [ ] CA-004: Se divergência > tolerância, rejeita valor e cria alerta
- [ ] CA-005: Valida invariantes: bruto >= liquido, descontos >= 0, etc.
- [ ] CA-006: Define gate_status: PASSED (todos campos OK), WARN (alguns falhos), FAILED (críticos falhos)

**Regras de Negócio:**
- RN-001: Regex aceita formatos: "R$ 1.334,36", "1.334,36", "1334,36"
- RN-002: Campos críticos (reprovam gate): salarioBruto, salarioLiquido
- RN-003: Campos opcionais (não reprovam): totalDescontos (pode ser calculado)
- RN-004: Alertas incluem: valor extraído, valor re-parseado, trecho de evidência

**Fluxo Principal:**
1. Recebe extracted_json do Extractor
2. Para cada campo numérico extraído:
   - Aplica regex no evidence.text
   - Normaliza ambos valores
   - Compara
3. Valida invariantes matemáticos
4. Consolida gate_status
5. Persiste alertas em `document_extractions.gate_alerts`

**Fluxos de Exceção:**
- FE-001: Evidence.text não contém número parseável → Rejeita valor
- FE-002: Violação de invariante (ex: bruto < liquido) → gate_status=FAILED

---

### RF-008: Seleção de Competência Alvo
**Prioridade:** P0
**Estimativa:** 3 pontos

**Descrição:**
Sistema deve consolidar competências (mês/ano) de todos os documentos e selecionar a mais recente como "competência alvo" para resultado final.

**Critérios de Aceite:**
- [ ] CA-001: Extrai competências detectadas de todos os PDFs (de router + extractors)
- [ ] CA-002: Normaliza para formato YYYY-MM (ex: "01/2026" → "2026-01")
- [ ] CA-003: Seleciona competência mais recente (ordenação cronológica)
- [ ] CA-004: Armazena em `analysis_jobs.competencia_alvo`
- [ ] CA-005: Se nenhuma competência detectada, usa mês/ano atual com alerta

**Regras de Negócio:**
- RN-001: Competência alvo é ÚNICA para todo o job (mesmo com múltiplos PDFs)
- RN-002: PDFs podem ter competências diferentes (ex: um de 12/2025, outro de 01/2026)
- RN-003: Resultado final sempre reflete a competência mais recente disponível

**Fluxo Principal:**
1. Coleta `competenciasDetectadas` de todos documents_extractions
2. Normaliza para YYYY-MM
3. Remove duplicatas
4. Ordena cronologicamente
5. Seleciona max(competencias)
6. Atualiza `analysis_jobs.competencia_alvo`

**Fluxos de Exceção:**
- FE-001: Nenhuma competência detectada → Usa data atual + alerta "competência inferida"

---

### RF-009: Consolidação de Fontes
**Prioridade:** P0
**Estimativa:** 8 pontos

**Descrição:**
Sistema deve consolidar valores da competência alvo quando múltiplos documentos fornecem o mesmo campo, resolvendo conflitos por prioridade de fonte.

**Critérios de Aceite:**
- [ ] CA-001: Identifica todos os candidatos (valores) para cada output na competência alvo
- [ ] CA-002: Aplica regras de prioridade (Apêndice 16 do blueprint) por campo
- [ ] CA-003: Se múltiplos candidatos com mesma prioridade divergem >1%, cria alerta
- [ ] CA-004: Armazena provenance (fonte escolhida) para cada campo
- [ ] CA-005: Popula tabela `payroll_months` com dados consolidados por competência

**Regras de Negócio:**
- RN-001: Prioridade salário bruto: PAYROLL > INSS_MR > null
- RN-002: Prioridade salário líquido: INSS_HISTORICO > PAYROLL > declarado (fallback)
- RN-003: Prioridade consignado mensal: folha/benefício (linhas) > estimado por contrato
- RN-004: Conflitos geram alertas mas não bloqueiam resultado

**Fluxo Principal:**
1. Filtra `payroll_months` por competencia_alvo
2. Para cada output (bruto, liquido, descontos, consignado):
   - Lista candidatos disponíveis
   - Ordena por prioridade
   - Seleciona melhor candidato
   - Registra provenance
3. Persiste em `final_results`

**Fluxos Alternativos:**
- FA-001: Se salarioLiquido não extraído, usa rendaMensalDeclarada com flag origem="declarado"

**Fluxos de Exceção:**
- FE-001: Conflito irreconciliável → Escolhe por prioridade + alerta detalhado

---

### RF-010: Cálculo Determinístico (Compute Engine)
**Prioridade:** P0
**Estimativa:** 5 pontos

**Descrição:**
Sistema deve executar todos os cálculos matemáticos em código determinístico usando centavos como BIGINT, garantindo precisão absoluta.

**Critérios de Aceite:**
- [ ] CA-001: Todos os valores monetários são armazenados como centavos (BIGINT)
- [ ] CA-002: Descontos calculados por: `descontos_cent = bruto_cent - liquido_cent` (quando método DIFFERENCE)
- [ ] CA-003: Consignado mensal calculado por: `soma(linhas_consignado_cent)` (quando método SUM_LINES)
- [ ] CA-004: Dívida total calculada por: `soma(valor_total_contrato_cent)` de contratos ativos
- [ ] CA-005: Parcelas restantes calculadas por: `soma(parcelas_restantes)` ou `soma(total_parcelas - parcelas_pagas)`
- [ ] CA-006: Conversão para UI: `valor_moeda = centavos / 100` com 2 casas decimais

**Regras de Negócio:**
- RN-001: ZERO tolerância a erro de arredondamento (por isso BIGINT centavos)
- RN-002: Cálculos só executam se inputs disponíveis e válidos
- RN-003: Método de cálculo é armazenado para auditoria
- RN-004: Operações suportadas: soma, subtração, multiplicação (em centavos)

**Fluxo Principal:**
1. Recebe valores consolidados (em centavos)
2. Calcula total_descontos_cent (se bruto e liquido presentes)
3. Calcula consignado_mensal_cent (se linhas disponíveis)
4. Calcula divida_total_consignada_cent (soma contratos)
5. Calcula parcelas_restantes_total (soma contratos)
6. Valida invariantes matemáticos
7. Persiste em `final_results`

**Fluxos de Exceção:**
- FE-001: Input inválido para cálculo → Deixa campo como null + alerta

---

### RF-011: Normalização de Contratos
**Prioridade:** P1
**Estimativa:** 5 pontos

**Descrição:**
Sistema deve normalizar contratos extraídos de extratos de empréstimo consignado, eliminando duplicatas e calculando valores faltantes.

**Critérios de Aceite:**
- [ ] CA-001: Gera contract_key (hash) baseado em: lender_name + contract_id + parcela + total_parcelas
- [ ] CA-002: Se valor_total_contrato ausente, calcula: `valor_total = parcela * total_parcelas`
- [ ] CA-003: Se parcelas_restantes ausente, calcula: `restantes = total_parcelas - parcelas_pagas`
- [ ] CA-004: Detecta duplicatas por contract_key entre documentos do mesmo job
- [ ] CA-005: Armazena em `loan_contracts` sem duplicatas

**Regras de Negócio:**
- RN-001: Contratos com status=QUITADO não entram em cálculos (configurável)
- RN-002: Deduplicação prioriza documento com mais dados completos
- RN-003: Todos os valores de contrato são em centavos

**Fluxo Principal:**
1. Recebe contratos extraídos de Loan Extractor
2. Para cada contrato:
   - Gera contract_key
   - Calcula campos faltantes
   - Verifica duplicata
3. Insere em `loan_contracts` (ON CONFLICT ignore)

**Fluxos de Exceção:**
- FE-001: Dados insuficientes para contract_key → Gera key baseado em file_id + índice

---

### RF-012: Exibição de Resultados com Evidências
**Prioridade:** P0
**Estimativa:** 8 pontos

**Descrição:**
Sistema deve exibir os 6 outputs finais em tela única com design limpo, incluindo evidências clicáveis e alertas contextuais.

**Critérios de Aceite:**
- [ ] CA-001: Exibe card para cada output: Salário Bruto, Líquido, Descontos, Consignado Mensal, Dívida Total, Parcelas Restantes
- [ ] CA-002: Cada valor exibe: moeda formatada (R$ X.XXX,XX), fonte (tipo documento + arquivo), ícone de evidência
- [ ] CA-003: Ao clicar em ícone de evidência, abre modal com: página do PDF, trecho destacado, método usado
- [ ] CA-004: Alertas exibidos em seção dedicada com severidade (warn/error)
- [ ] CA-005: Competência alvo exibida em destaque no topo
- [ ] CA-006: Campos null exibem "Não disponível" com explicação em tooltip

**Regras de Negócio:**
- RN-001: Evidência sempre mostra trecho original (não pode ser genérica)
- RN-002: Método de cálculo explicado em linguagem simples (ex: "Diferença entre bruto e líquido")
- RN-003: Alertas não bloqueiam exibição de resultados parciais

**Fluxo Principal:**
1. Frontend consulta GET /v1/analysis/jobs/{jobId}/result
2. Renderiza 6 cards com valores
3. Exibe badge de competência alvo
4. Lista alertas (se houver)
5. Usuário pode clicar em evidências para detalhes

**Fluxos Alternativos:**
- FA-001: Output null → Exibe "Não disponível" + razão em tooltip

---

### RF-013: API de Criação de Job
**Prioridade:** P0
**Estimativa:** 5 pontos

**Descrição:**
Endpoint REST para criar job de análise com upload de PDFs e dados declarados.

**Critérios de Aceite:**
- [ ] CA-001: POST /v1/analysis/jobs com multipart/form-data
- [ ] CA-002: Valida 1-3 arquivos .pdf (max 10MB cada, 25MB total)
- [ ] CA-003: Parseia renda_mensal_declarada e gasto_dividas_declarado (formato moeda BR)
- [ ] CA-004: Retorna 201 com jobId + status=PENDING
- [ ] CA-005: Retorna 400 para validações falhas (com mensagem específica)

**Regras de Negócio:**
- RN-001: jobId é UUID v4
- RN-002: user_id é extraído de JWT (quando autenticado) ou null (modo anônimo)
- RN-003: PDFs são salvos no S3 com path: `jobs/{jobId}/files/{fileId}.pdf`

**Fluxo Principal:**
1. Recebe request
2. Valida arquivos e campos
3. Cria registro em `analysis_jobs`
4. Upload PDFs para S3
5. Cria registros em `uploaded_files`
6. Enfileira job no pipeline
7. Retorna resposta 201

**Fluxos de Exceção:**
- FE-001: Arquivo > 10MB → 400 "File size exceeds 10MB"
- FE-002: Formato inválido → 400 "Invalid file format. PDF required"

---

### RF-014: API de Consulta de Status
**Prioridade:** P0
**Estimativa:** 3 pontos

**Descrição:**
Endpoint para polling de status e progresso do job.

**Critérios de Aceite:**
- [ ] CA-001: GET /v1/analysis/jobs/{jobId} retorna status atual
- [ ] CA-002: Inclui progress.step e progress.percent quando status=RUNNING
- [ ] CA-003: Retorna 404 se jobId não existir
- [ ] CA-004: Response time < 100ms (query otimizada)

**Regras de Negócio:**
- RN-001: Steps possíveis: EXTRACTION, ROUTING, PARSING, VALIDATION, CONSOLIDATION, COMPUTING
- RN-002: Percent é estimado baseado em step atual

**Fluxo Principal:**
1. Recebe jobId
2. Consulta `analysis_jobs.status`
3. Se RUNNING, consulta metadata de progresso
4. Retorna JSON estruturado

---

### RF-015: API de Resultado Final
**Prioridade:** P0
**Estimativa:** 5 pontos

**Descrição:**
Endpoint para obter resultado consolidado com evidências.

**Critérios de Aceite:**
- [ ] CA-001: GET /v1/analysis/jobs/{jobId}/result retorna 6 outputs
- [ ] CA-002: Cada output inclui: value (moeda), currency, source (tipo doc), evidence {fileId, page, text}
- [ ] CA-003: Retorna 200 quando status=SUCCEEDED
- [ ] CA-004: Retorna 202 quando status=PENDING/RUNNING (ainda processando)
- [ ] CA-005: Retorna 500 quando status=FAILED + error_message

**Regras de Negócio:**
- RN-001: Valores são convertidos de centavos para moeda (2 decimais)
- RN-002: Evidence.text é sanitizado (sem PII no response público)
- RN-003: Alertas limitados a 50 caracteres (truncados com "...")

**Fluxo Principal:**
1. Recebe jobId
2. Consulta `final_results` JOIN `analysis_jobs`
3. Formata valores (centavos → moeda)
4. Monta response estruturado
5. Retorna JSON

**Fluxos Alternativos:**
- FA-001: Job ainda processando → 202 com progress

---

### RF-016: Armazenamento RAG de Chunks Redigidos
**Prioridade:** P1
**Estimativa:** 8 pontos

**Descrição:**
Sistema deve armazenar representações redigidas (sem PII) de documentos processados em vector store para uso em auto-aprimoramento.

**Critérios de Aceite:**
- [ ] CA-001: Redige texto removendo CPF, NIT, RG, conta bancária, endereço
- [ ] CA-002: Gera embeddings usando modelo de embeddings (ex: text-embedding-3-small)
- [ ] CA-003: Armazena em Qdrant (ou pgvector) com metadata: docFamily, competencias, gate_status
- [ ] CA-004: Chunks têm 500-1000 caracteres com overlap de 100
- [ ] CA-005: Indexação permite busca por similaridade semântica

**Regras de Negócio:**
- RN-001: Redaction usa regex + NER para detectar PII
- RN-002: CPF substituído por "***.***.***-**"
- RN-003: Só documentos com gate_status=PASSED são armazenados
- RN-004: Embeddings permitem recuperar "casos similares" no futuro

**Fluxo Principal:**
1. Após Evidence Gate PASSED, processa texto
2. Aplica redaction
3. Chunking (500-1000 chars)
4. Gera embeddings
5. Persiste em Qdrant + `rag_chunks`

---

### RF-017: Repair Agent (Auto-aprimoramento)
**Prioridade:** P2
**Estimativa:** 13 pontos

**Descrição:**
Quando Evidence Gate falha, Repair Agent usa RAG para recuperar casos similares e propor melhorias no processo de extração.

**Critérios de Aceite:**
- [ ] CA-001: Acionado quando gate_status=FAILED em campos críticos
- [ ] CA-002: Recupera top-5 chunks similares via embedding search
- [ ] CA-003: Chama GPT-5.2 com prompt Repair Agent (seção 10.4)
- [ ] CA-004: Propõe: novo docFamily, anchors (keywords/regex), patch de prompt
- [ ] CA-005: Proposta é armazenada mas NÃO aplicada automaticamente

**Regras de Negócio:**
- RN-001: Propostas só são promovidas após validação em testes golden
- RN-002: Testes anti-regressão obrigatórios antes de promote
- RN-003: Humano aprova promoção (Fase 2) ou automático (Fase 3 com travas)

**Fluxo Principal:**
1. Detecta gate_status=FAILED
2. Busca chunks similares (embedding search)
3. Monta prompt Repair Agent
4. Chama GPT-5.2
5. Parseia proposta
6. Armazena em tabela `repair_proposals` (P2 - não no MVP)

**Fluxos de Exceção:**
- FE-001: Nenhum chunk similar → Repair Agent trabalha sem exemplos

---

### RF-018: Testes Golden (Anti-regressão)
**Prioridade:** P2
**Estimativa:** 8 pontos

**Descrição:**
Suite de testes automáticos com PDFs históricos e outputs esperados para validar que mudanças não quebram extração.

**Critérios de Aceite:**
- [ ] CA-001: Conjunto de min 20 PDFs representativos com expected outputs
- [ ] CA-002: Testes executam pipeline completo para cada PDF
- [ ] CA-003: Compara outputs vs. expected com tolerância de ±0.01
- [ ] CA-004: Testes rodam em CI/CD antes de deploy
- [ ] CA-005: Falha em teste golden bloqueia deploy

**Regras de Negócio:**
- RN-001: PDFs golden cobrem todas as famílias suportadas
- RN-002: Expected outputs incluem: valores + provenance + métodos
- RN-003: Suite roda em <5 minutos

---

### RF-019: WebSocket de Progresso em Tempo Real
**Prioridade:** P2
**Estimativa:** 5 pontos

**Descrição:**
Conexão WebSocket para receber atualizações de progresso do job em tempo real sem polling.

**Critérios de Aceite:**
- [ ] CA-001: GET /v1/analysis/jobs/{jobId}/ws estabelece conexão WS
- [ ] CA-002: Envia mensagens JSON com: step, percent, timestamp
- [ ] CA-003: Envia mensagem final com status SUCCEEDED/FAILED
- [ ] CA-004: Conexão fecha automaticamente após conclusão ou após 10min idle

**Regras de Negócio:**
- RN-001: Fallback para polling se WS não disponível
- RN-002: Mensagens enviadas apenas quando progresso muda (debounce)

---

### RF-020: Download de Relatório de Auditoria
**Prioridade:** P2
**Estimativa:** 5 pontos

**Descrição:**
Endpoint para baixar JSON completo com todas as evidências, candidatos descartados e decisões do consolidador.

**Critérios de Aceite:**
- [ ] CA-001: GET /v1/analysis/jobs/{jobId}/audit retorna JSON estruturado
- [ ] CA-002: Inclui: todos extractors outputs, gate results, consolidation decisions, provenance
- [ ] CA-003: Formato permite auditoria técnica completa
- [ ] CA-004: PII é redigido antes de export

**Regras de Negócio:**
- RN-001: Apenas usuário dono do job pode baixar auditoria
- RN-002: Auditoria disponível por 90 dias após job

---

## Requisitos Não-Funcionais

### RNF-001: Performance
**Prioridade:** P0

- **RNF-001.1:** Processamento de 3 PDFs (total <15MB) deve completar em <45 segundos (P90)
- **RNF-001.2:** API de consulta de status deve responder em <100ms (P95)
- **RNF-001.3:** Upload de PDF deve iniciar processamento em <2 segundos após confirmação
- **RNF-001.4:** OCR (quando necessário) não deve adicionar >20 segundos ao tempo total

**Métricas de Aceitação:**
- Medição via OpenTelemetry traces
- Alertas se P90 > 60 segundos

---

### RNF-002: Segurança e Privacidade
**Prioridade:** P0

- **RNF-002.1:** PDFs armazenados com criptografia em repouso (AES-256)
- **RNF-002.2:** Logs NUNCA contêm PII (CPF, NIT, valores financeiros detalhados)
- **RNF-002.3:** Comunicação HTTPS/TLS 1.3 obrigatória
- **RNF-002.4:** Autenticação via JWT com expiração de 24h (quando não-anônimo)
- **RNF-002.5:** Rate limiting: 10 jobs por usuário por hora
- **RNF-002.6:** PDFs deletados automaticamente após 30 dias (configurável)
- **RNF-002.7:** Chunks RAG contêm apenas texto redigido (regex + NER para PII)

**Validação:**
- Penetration testing trimestral
- Scan automático de secrets em código (pre-commit hook)

---

### RNF-003: Escalabilidade
**Prioridade:** P1

- **RNF-003.1:** Sistema deve suportar 100 jobs simultâneos (Fase 1)
- **RNF-003.2:** Horizontal scaling de workers (stateless)
- **RNF-003.3:** Queue deve suportar 1000 jobs enfileirados
- **RNF-003.4:** Banco deve suportar 1M+ jobs históricos sem degradação

**Arquitetura:**
- Workers autoscaling baseado em tamanho da fila
- PostgreSQL com particionamento por data em `analysis_jobs`

---

### RNF-004: Disponibilidade
**Prioridade:** P1

- **RNF-004.1:** SLA de 99.5% uptime (Fase 1), 99.9% (Fase 3)
- **RNF-004.2:** Degradação graceful: se LLM indisponível, retorna erro claro (não trava)
- **RNF-004.3:** Retry automático em falhas transientes (max 3x com backoff exponencial)
- **RNF-004.4:** Health checks em /health e /ready para load balancer

**Monitoramento:**
- Prometheus + Grafana para métricas
- PagerDuty para alertas críticos

---

### RNF-005: Observabilidade
**Prioridade:** P0

- **RNF-005.1:** Logs estruturados em JSON com trace_id para correlação
- **RNF-005.2:** Traces distribuídos (OpenTelemetry) de ponta a ponta
- **RNF-005.3:** Métricas de negócio: taxa de sucesso por família, % OCR, tempo por etapa
- **RNF-005.4:** Dashboards tempo real para operação

**Ferramentas:**
- Logs: JSON stdout → agregador (CloudWatch, ELK)
- Traces: OpenTelemetry → Jaeger/Tempo
- Métricas: Prometheus
- Alertas: divergência extraído vs. declarado >30% em >10% dos jobs

---

### RNF-006: Confiabilidade Matemática
**Prioridade:** P0

- **RNF-006.1:** ZERO tolerância a erro de cálculo (100% precisão)
- **RNF-006.2:** Todos os valores monetários em centavos (BIGINT)
- **RNF-006.3:** Conversão para moeda apenas na camada de apresentação
- **RNF-006.4:** Testes de propriedade (property-based) para invariantes matemáticos
- **RNF-006.5:** Suite de testes golden com 100% pass rate obrigatório

**Validação:**
- CI/CD bloqueia merge se testes golden falharem
- Testes de invariantes: bruto >= liquido, descontos >= 0, etc.

---

### RNF-007: Manutenibilidade
**Prioridade:** P1

- **RNF-007.1:** Cobertura de testes unitários >80%
- **RNF-007.2:** Documentação de API (OpenAPI/Swagger)
- **RNF-007.3:** Código segue style guide (Black para Python, Prettier para TS)
- **RNF-007.4:** Versionamento de extractors (permite rollback)

---

### RNF-008: Compatibilidade
**Prioridade:** P1

- **RNF-008.1:** Frontend suporta últimas 2 versões de Chrome, Firefox, Safari, Edge
- **RNF-008.2:** Mobile responsive (viewport mín 375px)
- **RNF-008.3:** API versionada (/v1/) para backward compatibility

---

### RNF-009: Custo
**Prioridade:** P1

- **RNF-009.1:** Custo de LLM por job <R$ 0,50 (média)
- **RNF-009.2:** OCR acionado em <15% dos casos
- **RNF-009.3:** Embeddings gerados apenas para casos PASSED (reduz custo)

**Otimizações:**
- Cache de 15min para URLs (WebFetch pattern)
- Usar GPT-4o-mini para Router (mais barato), GPT-5.2 para Extractors

---

### RNF-010: Requisitos de Runtime e Ambiente
**Prioridade:** P0

**Versões Obrigatórias (atualizado em janeiro 2026):**
- **RNF-010.1:** Node.js 20.9.0+ (LTS) - Node.js 18 não é mais suportado pelo Next.js 16
- **RNF-010.2:** TypeScript 5.1.0+ (mínimo para Next.js 16)
- **RNF-010.3:** Python 3.11+ (recomendado 3.12 para FastAPI e Pydantic v2 performance)
- **RNF-010.4:** PostgreSQL 18 (recomendado para AIO, skip scan, temporal constraints)
- **RNF-010.5:** pytest 9.0+ (suporte nativo TOML configuration)
- **RNF-010.6:** Pydantic v2.x (performance otimizada com Rust core)

**Compatibilidade de Browsers (Next.js 16 + Tailwind CSS v4):**
- Chrome 111+ (março 2023)
- Edge 111+ (março 2023)
- Firefox 128+ (julho 2024) - **atualizado para Tailwind v4**
- Safari 16.4+ (março 2023)

**Nota:** Tailwind CSS v4 requer Firefox 128+ devido a dependências de `@property` e `color-mix()`. Se precisar suportar Firefox 111-127, permaneça em Tailwind CSS v3.4.

**Breaking Changes e Considerações:**

**Frontend:**
- **Next.js 16:** APIs de cache (`cacheLife`, `cacheTag`) agora estáveis (sem prefixo `unstable_`)
- **React 19:** Melhorias de performance, novos hooks, estável (usar 19.2+)
- **Tailwind CSS v4:**
  - Novos seletores (`space-x/y` usa `:not(:last-child)` vs `~ :not([hidden])`)
  - Renomeação de escalas: `shadow-sm` → `shadow-xs`, `shadow` → `shadow-sm`
  - Requer CSS moderno (`@property`, `color-mix()`)

**Backend:**
- **FastAPI 0.128:** Parâmetros obrigatórios podem omitir `default` (sintaxe simplificada)
- **Pydantic v2:** Migração de métodos (`.dict()` → `.model_dump()`, `.parse_obj()` → `.model_validate()`)
- **PostgreSQL 18:**
  - Async I/O subsystem (melhor performance para scans sequenciais)
  - Skip scan (índices B-tree multicoluna mais eficientes)
  - Virtual generated columns (default)
  - OAuth authentication nativo
  - Temporal constraints (PRIMARY KEY, UNIQUE, FK sobre ranges)
- **pytest 9.0:** Configuração via `pytest.toml` ou `[tool.pytest]` nativo em `pyproject.toml`

**Ambientes:**
- Desenvolvimento: Docker com Node 20 + Python 3.11+
- CI/CD: Actions/Pipelines com mesmas versões
- Produção: Containers com versões fixadas (pin exact versions)

---

## Arquitetura Técnica

### Diagrama de Arquitetura de Alto Nível

```mermaid
graph TB
    User[Usuário Web] -->|Upload PDFs| WebUI[Next.js Frontend]
    WebUI -->|POST /v1/analysis/jobs| API[FastAPI Backend]
    API -->|Save| S3[(S3/MinIO<br/>PDFs criptografados)]
    API -->|Create job| DB[(PostgreSQL)]
    API -->|Enqueue| Queue[Redis/RabbitMQ]

    Queue -->|Consume| Worker[Temporal Worker]

    Worker -->|1. Extract| Extractor[PyMuPDF/pdfplumber]
    Extractor -.->|Fallback OCR| OCR[AWS Textract]

    Worker -->|2. Route| Router[GPT-5.2 Router]
    Worker -->|3. Parse| LLMExtractor[GPT-5.2 Extractors]
    Worker -->|4. Validate| Gate[Evidence Gate<br/>Determinístico]
    Worker -->|5. Consolidate| Consolidator[Consolidator Logic]
    Worker -->|6. Calculate| Compute[Compute Engine<br/>BIGINT centavos]

    Worker -->|Persist| DB
    Worker -->|Store chunks| RAG[(Qdrant<br/>Vector Store)]

    Worker -.->|On failure| Repair[Repair Agent<br/>GPT-5.2]
    Repair -.->|Query similar| RAG

    API -->|GET result| WebUI
    WebUI -->|Display| User

    Worker -->|Metrics| Prometheus[Prometheus]
    Worker -->|Traces| OTel[OpenTelemetry]
    Prometheus --> Grafana[Grafana Dashboards]
```

---

### Stack Tecnológica Recomendada

| Camada | Tecnologia | Justificativa |
|--------|------------|---------------|
| **Frontend** | Next.js 16.1+ (App Router) + React 19.2+ | SSR, performance, stable cache APIs, developer experience |
| **UI Framework** | Tailwind CSS v4 + shadcn/ui | Modern CSS, zero-runtime, utility-first design system |
| **Backend API** | FastAPI 0.128+ (Python 3.11+) | Performance, async native, type hints, simplified params |
| **Orquestração** | Temporal.io | Confiabilidade em workflows complexos, observabilidade |
| **Queue (alternativa)** | Celery 4.4+ + Redis | Opção mais simples se Temporal for overkill |
| **Database** | PostgreSQL 18 | AIO subsystem, skip scan, temporal constraints, OAuth auth |
| **Object Storage** | MinIO (self-hosted) ou S3 | Criptografia, escalabilidade |
| **PDF Extraction** | PyMuPDF (fitz) | Rápido, preserva layout |
| **OCR Fallback** | AWS Textract | Precisão alta, pay-per-use |
| **LLM** | OpenAI GPT-5.2 (ou GPT-4o) | Capacidade de seguir schemas complexos |
| **Embeddings** | text-embedding-3-small | Custo/benefício para RAG |
| **Vector Store** | Qdrant 1.x | Performance, filtros metadata, hybrid search |
| **Data Validation** | Pydantic v2 | Type-safe validation, performance (Rust core) |
| **Observability** | OpenTelemetry + Prometheus + Grafana | Padrão indústria, vendor-neutral |
| **Error Tracking** | Sentry | Contexto rico, alertas |
| **Testing** | pytest 9.0+ (backend), Vitest (frontend) | TOML config, maturidade, ecossistema |

---

### Integrações Externas

| Serviço | Tipo | Uso | Criticidade |
|---------|------|-----|-------------|
| OpenAI API | LLM | Router, Extractors, Repair Agent | **Crítica** |
| AWS Textract | OCR | Fallback para PDFs sem texto | Média |
| S3/MinIO | Storage | Armazenamento de PDFs | **Crítica** |
| SMTP (SendGrid/SES) | Email | Notificações (futuro) | Baixa |

---

### Modelo de Dados (Detalhado)

#### Diagrama ER (Entidades Principais)

```mermaid
erDiagram
    USERS ||--o{ ANALYSIS_JOBS : creates
    ANALYSIS_JOBS ||--|{ UPLOADED_FILES : contains
    ANALYSIS_JOBS ||--o| FINAL_RESULTS : produces
    UPLOADED_FILES ||--o{ DOCUMENT_EXTRACTIONS : analyzed
    DOCUMENT_EXTRACTIONS ||--o{ RAG_CHUNKS : generates
    ANALYSIS_JOBS ||--o{ LOAN_CONTRACTS : extracts
    ANALYSIS_JOBS ||--o{ PAYROLL_MONTHS : extracts

    USERS {
        uuid id PK
        text email
        timestamp created_at
    }

    ANALYSIS_JOBS {
        uuid id PK
        uuid user_id FK
        text status
        bigint renda_declarada_cent
        bigint gasto_declarado_cent
        text competencia_alvo
        timestamp created_at
    }

    UPLOADED_FILES {
        uuid id PK
        uuid job_id FK
        text original_filename
        text storage_url
        text file_sha256
    }

    DOCUMENT_EXTRACTIONS {
        uuid id PK
        uuid file_id FK
        text router_family
        jsonb extracted_json
        jsonb evidence_json
        text gate_status
        jsonb gate_alerts
    }

    LOAN_CONTRACTS {
        uuid id PK
        uuid job_id FK
        text lender_name
        bigint parcela_cent
        int total_parcelas
        int parcelas_restantes
        bigint valor_total_cent
    }

    PAYROLL_MONTHS {
        uuid id PK
        uuid job_id FK
        text competencia
        bigint bruto_cent
        bigint liquido_cent
        bigint descontos_cent
        bigint consignado_cent
        jsonb evidence
    }

    FINAL_RESULTS {
        uuid job_id PK_FK
        text competencia_alvo
        bigint salario_bruto_cent
        bigint salario_liquido_cent
        bigint total_descontos_cent
        bigint consignado_mensal_cent
        bigint divida_total_cent
        int parcelas_restantes_total
        jsonb provenance
        jsonb alerts
    }

    RAG_CHUNKS {
        uuid id PK
        uuid file_id FK
        text chunk_text_redacted
        vector embedding
        jsonb metadata
    }
```

#### Scripts de Migração (Alembic)

Ver seção de Implementação para DDL completo.

---

### Segurança (Detalhamento)

**Autenticação e Autorização:**
- JWT Bearer tokens (opcional, suporta modo anônimo)
- Scopes: `jobs:create`, `jobs:read:own`, `jobs:read:all` (admin)
- RBAC: user, analyst, admin

**Proteção de Dados:**
- PDFs: S3 SSE-S3 (AES-256)
- DB: encryption at rest (RDS/managed PostgreSQL)
- Transit: TLS 1.3 obrigatório

**PII Handling:**
- Logs: filtro automático de padrões (CPF, cartões)
- RAG: redaction via regex + spaCy NER
- Exports: sempre aplicar redaction

**Rate Limiting:**
- Por IP: 100 req/min
- Por user: 10 jobs/hora
- Implementação: Redis + FastAPI middleware

**Input Validation:**
- File upload: magic bytes check (não só extensão)
- SQL injection: parametrized queries (SQLAlchemy ORM)
- XSS: sanitização automática (React escaping)

---

## User Stories e Épicos

### Épico 1: Upload e Processamento de Documentos
**Como** analista de crédito
**Quero** fazer upload de contracheques e extratos
**Para** obter automaticamente os indicadores financeiros sem digitação manual

#### US-001: Upload de múltiplos PDFs
- **Prioridade:** Alta
- **Pontos:** 3
- **Dependências:** Nenhuma

**Critérios de aceite:**
- Posso arrastar 1 a 3 arquivos PDF para área de upload
- Sistema valida tamanho e formato antes de aceitar
- Vejo preview (thumbnail) de cada arquivo aceito
- Posso remover arquivo individual antes de submeter

---

#### US-002: Informar dados declarados
- **Prioridade:** Alta
- **Pontos:** 2
- **Dependências:** US-001

**Critérios de aceite:**
- Posso digitar renda mensal declarada com formatação automática de moeda
- Posso digitar gasto mensal declarado
- Campos aceitam valores opcionais
- Sistema aceita valores entre R$ 0,01 e R$ 999.999,99

---

#### US-003: Acompanhar progresso do processamento
- **Prioridade:** Alta
- **Pontos:** 5
- **Dependências:** US-002

**Critérios de aceite:**
- Após submeter, vejo tela de progresso com barra e etapa atual
- Etapas exibidas: Extração, Análise, Validação, Consolidação, Cálculo
- Progresso atualiza automaticamente (polling ou WS)
- Se processamento falhar, vejo mensagem de erro clara

---

### Épico 2: Visualização de Resultados
**Como** analista de crédito
**Quero** visualizar os indicadores extraídos com evidências
**Para** confiar nos valores e auditar a extração

#### US-004: Ver indicadores consolidados
- **Prioridade:** Alta
- **Pontos:** 5
- **Dependências:** US-003

**Critérios de aceite:**
- Vejo 6 cards com: Salário Bruto, Líquido, Descontos, Consignado Mensal, Dívida Total, Parcelas Restantes
- Valores em formato moeda brasileiro (R$ X.XXX,XX)
- Competência (mês/ano) destacada no topo
- Campos não disponíveis mostram "Não disponível" com explicação

---

#### US-005: Acessar evidências de extração
- **Prioridade:** Alta
- **Pontos:** 8
- **Dependências:** US-004

**Critérios de aceite:**
- Cada valor tem ícone de "evidência"
- Ao clicar, vejo modal com: nome do arquivo, página, trecho do PDF
- Trecho destaca o valor extraído
- Modal mostra método usado (ex: "Extraído do campo 'Valor Líquido'")

---

#### US-006: Revisar alertas e divergências
- **Prioridade:** Média
- **Pontos:** 3
- **Dependências:** US-004

**Critérios de aceite:**
- Vejo seção "Alertas" quando houver inconsistências
- Alertas classificados por severidade (aviso/erro)
- Alertas explicam: qual campo, qual divergência, fontes envolvidas
- Exemplo: "Salário líquido diverge 15% entre documento A e B. Escolhido: A (prioridade)"

---

### Épico 3: Extração Inteligente (Backend)
**Como** desenvolvedor do sistema
**Quero** que o sistema identifique automaticamente tipos de documentos
**Para** suportar milhares de layouts sem configuração manual

#### US-007: Classificar documento em família
- **Prioridade:** Alta
- **Pontos:** 8
- **Dependências:** Infraestrutura

**Critérios de aceite:**
- Router GPT-5.2 recebe texto extraído
- Retorna família (PAYROLL, INSS_HISTORICO, INSS_CONSIGNADO, OTHER)
- Inclui confidence score (0-1)
- Armazena 3 evidências (trechos) que justificam classificação

---

#### US-008: Extrair campos estruturados
- **Prioridade:** Alta
- **Pontos:** 13
- **Dependências:** US-007

**Critérios de aceite:**
- Extractor específico é selecionado baseado em família
- Extrai: bruto, líquido, descontos, linhas consignado (payment) OU contratos (loan)
- Cada valor inclui evidência (página + trecho)
- Se campo não existe, retorna null + alerta

---

#### US-009: Validar valores extraídos
- **Prioridade:** Alta
- **Pontos:** 8
- **Dependências:** US-008

**Critérios de aceite:**
- Evidence Gate re-parseia trecho de evidência com regex
- Compara valor LLM vs. valor re-parseado
- Rejeita se divergência > 1 centavo
- Valida invariantes (bruto >= liquido)
- Define status: PASSED/WARN/FAILED

---

### Épico 4: Confiabilidade Matemática
**Como** gestor de produto
**Quero** garantir zero erros de cálculo
**Para** evitar riscos de compliance e prejuízo financeiro

#### US-010: Calcular valores determinísticos
- **Prioridade:** Alta
- **Pontos:** 5
- **Dependências:** US-009

**Critérios de aceite:**
- Todos os valores em centavos (BIGINT)
- Descontos = bruto - liquido (quando método DIFF)
- Consignado mensal = soma(linhas_consignado)
- Dívida total = soma(valor_total_contratos)
- Parcelas restantes = soma(parcelas_restantes_contratos)
- Nenhum arredondamento intermediário

---

#### US-011: Suite de testes golden
- **Prioridade:** Alta (Fase 2)
- **Pontos:** 8
- **Dependências:** US-010

**Critérios de aceite:**
- 20+ PDFs históricos com expected outputs
- Testes rodam em CI/CD
- 100% pass rate obrigatório para merge
- Testes cobrem todas as famílias de documentos

---

### Épico 5: Auto-aprimoramento (Camada C)
**Como** gestor de operações
**Quero** que o sistema aprenda com falhas
**Para** reduzir necessidade de intervenção manual

#### US-012: Armazenar casos em RAG
- **Prioridade:** Média (Fase 2)
- **Pontos:** 8
- **Dependências:** Infraestrutura Qdrant

**Critérios de aceite:**
- Documentos PASSED são redigidos (PII removido)
- Chunks de 500-1000 chars com embeddings
- Armazenados em Qdrant com metadata (família, competências)
- Busca por similaridade funcional

---

#### US-013: Propor melhorias via Repair Agent
- **Prioridade:** Baixa (Fase 3)
- **Pontos:** 13
- **Dependências:** US-012

**Critérios de aceite:**
- Repair Agent acionado quando gate_status=FAILED
- Recupera top-5 casos similares
- GPT-5.2 propõe: novo docFamily, anchors, patch de prompt
- Proposta armazenada (não aplicada automaticamente)

---

#### US-014: Validar e promover melhorias
- **Prioridade:** Baixa (Fase 3)
- **Pontos:** 8
- **Dependências:** US-013, US-011

**Critérios de aceite:**
- Proposta é testada contra suite golden
- Se pass rate >= atual, pode ser promovida
- Aprovação humana (Fase 3a) ou automática com travas (Fase 3b)
- Rollback disponível se degradação detectada

---

## Cronograma e Fases

### Fase 1: MVP Confiável (8-10 semanas)

**Objetivo:** Sistema funcional com extração, validação e cálculo para 3 famílias principais.

| Semana | Entregável | Responsável | Status |
|--------|------------|-------------|--------|
| 1-2 | Infraestrutura (FastAPI, PostgreSQL, S3, Redis) | Backend Lead | - |
| 1-2 | Frontend base (Next.js, upload UI, tela resultados) | Frontend Lead | - |
| 2-3 | Extração de PDF (PyMuPDF) + OCR fallback | Backend Eng | - |
| 3-4 | Router GPT-5.2 + Extractors (Payment + Loan) | ML Eng | - |
| 4-5 | Evidence Gate (validação determinística) | Backend Eng | - |
| 5-6 | Consolidador (competência + prioridades) | Backend Eng | - |
| 6-7 | Compute Engine (cálculos em centavos) | Backend Eng | - |
| 7-8 | API completa (/jobs, /status, /result) | Backend Lead | - |
| 8 | Integração Frontend ↔ Backend | Full Stack | - |
| 9 | Testes E2E + QA | QA Lead | - |
| 10 | Deploy staging + beta interna | DevOps | - |

**Critérios de conclusão:**
- [ ] 3 famílias suportadas: PAYROLL, INSS_HISTORICO, INSS_CONSIGNADO
- [ ] Taxa de sucesso ≥70% em dataset de validação (50 PDFs diversos)
- [ ] 100% precisão matemática em testes unitários
- [ ] Tempo de processamento <45s (P90)

---

### Fase 2: RAG e Observabilidade (4-6 semanas)

**Objetivo:** Adicionar RAG para auto-aprimoramento, melhorar observabilidade e adicionar OCR robusto.

| Semana | Entregável | Responsável | Status |
|--------|------------|-------------|--------|
| 11-12 | Qdrant setup + pipeline de redaction | Backend Eng | - |
| 12-13 | Embedding generation + storage | ML Eng | - |
| 13-14 | Repair Agent (proposta, sem promote automático) | ML Eng | - |
| 14-15 | OpenTelemetry + Prometheus + Grafana dashboards | DevOps | - |
| 15-16 | Suite de testes golden (20 PDFs) | QA + ML Eng | - |
| 16 | Beta com clientes selecionados | Product Manager | - |

**Critérios de conclusão:**
- [ ] RAG armazenando chunks redigidos
- [ ] Repair Agent propondo melhorias (manual review)
- [ ] Dashboards operacionais completos
- [ ] Suite golden com 100% pass rate

---

### Fase 3: Auto-aprimoramento Automático (6-8 semanas)

**Objetivo:** Promover melhorias automaticamente com travas de segurança.

| Semana | Entregável | Responsável | Status |
|--------|------------|-------------|--------|
| 17-18 | Promote engine (testes anti-regressão) | ML Eng | - |
| 18-19 | Rollback automático em degradação | DevOps + ML Eng | - |
| 19-20 | Expensão para novas famílias (BANK_STATEMENT) | ML Eng | - |
| 20-22 | Otimizações de custo LLM (cache, chunking) | Backend Eng | - |
| 22-24 | Hardening de segurança (pentest, audit) | Security Eng | - |
| 24 | GA (General Availability) | Product Manager | - |

**Critérios de conclusão:**
- [ ] Auto-promote com aprovação automática se ΔPass Rate ≥ 0
- [ ] Taxa de sucesso ≥95%
- [ ] Custo por job <R$ 0,50
- [ ] SLA 99.9% uptime

---

## Riscos e Mitigações

| ID | Risco | Probabilidade | Impacto | Mitigação | Owner |
|----|-------|---------------|---------|-----------|-------|
| R-001 | LLM alucina valores financeiros | Média | **Alto** | Evidence Gate obrigatório + re-parsing determinístico | ML Eng |
| R-002 | OpenAI API indisponível | Baixa | Alto | Retry com backoff + queue durável + fallback para outro provider (futuro) | DevOps |
| R-003 | PDFs com layouts completamente novos (baixa extração) | Alta | Médio | Repair Agent + RAG + expansão gradual de famílias | ML Eng |
| R-004 | Custo de LLM excede orçamento | Média | Médio | Cache de embeddings + usar modelos menores para Router + otimizar prompts | Backend Lead |
| R-005 | OCR com baixa precisão em PDFs ruins | Média | Médio | Usar AWS Textract (alta precisão) + alertar usuário para reenviar PDF de qualidade | ML Eng |
| R-006 | Vazamento de PII em logs/RAG | Baixa | **Alto** | Redaction obrigatória + testes automatizados de PII + audit trimestral | Security Eng |
| R-007 | Performance degradada com PDFs grandes (>10MB) | Média | Médio | Limite de 10MB + processamento chunked + timeout | Backend Eng |
| R-008 | Conflitos entre documentos não resolvidos adequadamente | Média | Médio | Regras de prioridade bem definidas + alertas claros + UX para revisão manual | Product Manager |
| R-009 | Suite golden não cobre casos edge | Alta | Médio | Expandir continuamente golden set + monitoring de casos FAILED em produção | QA Lead |
| R-010 | Dependência crítica de único provider LLM | Média | Alto | Abstrair interface LLM + planejar fallback para Anthropic/Gemini (Fase 3) | ML Eng |

---

## Dependências Externas

### Dependências de Terceiros
- **OpenAI API (GPT-5.2 ou GPT-4o):** Crítico para Router e Extractors
  - SLA: 99.9% (conforme OpenAI)
  - Contingência: Queue durável permite retry; futuro fallback para outro provider

- **AWS Textract:** Opcional (OCR fallback)
  - SLA: 99.9%
  - Contingência: Processar sem OCR (marcar alerta de qualidade)

### Dependências Internas (Times)
- **DevOps:** Setup de infraestrutura (S3, PostgreSQL, Redis, Temporal)
- **Security:** Revisão de redaction, pentest, compliance
- **Legal:** Aprovação de termos de uso (retenção de PDFs, privacidade)

---

## Fora do Escopo

**Explicitamente NÃO incluído na Fase 1:**
- ❌ Suporte a documentos que não sejam PDF
- ❌ Extração de dados além dos 6 outputs definidos (ex: beneficiários, dependentes)
- ❌ Interface mobile nativa (iOS/Android) - apenas web responsiva
- ❌ Integração com bureaus de crédito (Serasa, SPC)
- ❌ Recomendação de produtos financeiros (apenas extração)
- ❌ Multi-idioma (apenas português BR)
- ❌ Modo offline

**Fora do escopo de todas as fases:**
- ❌ Assinatura digital de documentos
- ❌ Geração de contratos de empréstimo
- ❌ Processamento de imagens que não sejam PDF (JPEG, PNG)

---

## Glossário

| Termo | Definição |
|-------|-----------|
| **Competência** | Mês/ano de referência de um pagamento ou documento (ex: "01/2026"). Normalizado internamente como YYYY-MM. |
| **Competência Alvo** | A competência mais recente dentre todos os PDFs enviados, usada como referência para o resultado final. |
| **Família de Documento** | Categoria de documento (ex: PAYROLL_SALARY_STATEMENT, INSS_HISTORICO_CREDITOS) que determina qual extractor usar. |
| **Capability** | Dado que um documento pode fornecer (ex: PROVIDES_GROSS_NET_DEDUCTIONS, PROVIDES_LOAN_CONTRACTS). |
| **Evidência** | Trecho de texto (com página) que sustenta um valor extraído, usado para validação e auditoria. |
| **Evidence Gate** | Componente determinístico que valida que cada valor extraído tem evidência localizável e parseável. |
| **Router** | Componente LLM que classifica documento em família e identifica capabilities. |
| **Extractor** | Componente LLM específico por família que extrai campos estruturados. |
| **Consolidador** | Lógica que resolve conflitos entre múltiplos documentos priorizando fontes confiáveis. |
| **Compute Engine** | Componente determinístico que executa cálculos matemáticos em centavos (BIGINT). |
| **RAG (Retrieval-Augmented Generation)** | Técnica de armazenar embeddings de casos anteriores para recuperação e auto-aprimoramento. |
| **Repair Agent** | Componente LLM que propõe melhorias quando Evidence Gate falha. |
| **Golden Test** | Teste com PDF histórico e output esperado, usado para anti-regressão. |
| **Provenance** | Rastreamento de onde um valor veio (tipo de documento + arquivo + método). |
| **Centavos** | Representação de valores monetários como inteiros (BIGINT) para evitar erros de arredondamento. |
| **Consignado** | Empréstimo com desconto automático em folha de pagamento ou benefício INSS. |
| **MR (Margem de Remuneração)** | Campo do INSS que representa o salário base/bruto. |
| **Rubrica** | Código numérico que identifica tipo de provento ou desconto em folha (ex: 216 = consignação empréstimo). |

---

## Métricas de Sucesso (KPIs)

### Métricas de Produto

| KPI | Fórmula | Meta Fase 1 | Meta Fase 3 | Frequência |
|-----|---------|-------------|-------------|------------|
| **Taxa de Extração Bem-Sucedida** | (jobs com ≥4 outputs / total jobs) × 100 | ≥70% | ≥95% | Diária |
| **Precisão de Valores** | (valores corretos / valores extraídos) × 100 (validação manual amostral) | ≥90% | ≥97% | Semanal |
| **Tempo Médio de Processamento** | P90 de tempo total de job | <45s | <20s | Diária |
| **Taxa de OCR** | (jobs que usaram OCR / total jobs) × 100 | <20% | <15% | Semanal |
| **Taxa de Alertas** | (jobs com alertas / total jobs) × 100 | <40% | <20% | Diária |
| **Cobertura de Famílias** | % de jobs classificados != OTHER_UNKNOWN | ≥80% | ≥95% | Semanal |

### Métricas de Negócio

| KPI | Fórmula | Meta Fase 1 | Meta Fase 3 | Frequência |
|-----|---------|-------------|-------------|------------|
| **Redução de Tempo vs. Manual** | (tempo manual - tempo sistema) / tempo manual × 100 | ≥80% | ≥95% | Mensal |
| **Custo por Job** | (custo LLM + infra) / total jobs | <R$ 0,70 | <R$ 0,50 | Semanal |
| **NPS (Net Promoter Score)** | % promotores - % detratores | ≥50 | ≥70 | Trimestral |

### Métricas Técnicas

| KPI | Fórmula | Meta Fase 1 | Meta Fase 3 | Frequência |
|-----|---------|-------------|-------------|------------|
| **Uptime** | (tempo online / tempo total) × 100 | ≥99.5% | ≥99.9% | Mensal |
| **Latência API (P95)** | 95º percentil de tempo de resposta | <200ms | <100ms | Diária |
| **Taxa de Erro 5xx** | (respostas 5xx / total requests) × 100 | <1% | <0.1% | Diária |
| **Cobertura de Testes** | (linhas cobertas / total linhas) × 100 | ≥75% | ≥85% | Por commit |

---

## Anexos

### Anexo A: Exemplos de PDFs Suportados

**Família: PAYROLL_SALARY_STATEMENT**
- Contracheques de empresas privadas (diversos layouts)
- Holerites de órgãos públicos (federais, estaduais, municipais)

**Família: INSS_HISTORICO_CREDITOS**
- Histórico de Créditos INSS (layout padrão DATAPREV)
- Extrato de Pagamento de Benefício

**Família: INSS_EXTRATO_CONSIGNADO**
- Extrato de Empréstimos Consignados INSS
- Extratos de bancos específicos (Banco do Brasil, Caixa, Bradesco, Itaú, etc.)

---

### Anexo B: Schemas de API (OpenAPI)

```yaml
openapi: 3.0.3
info:
  title: Calculadora de Consignados API
  version: 1.0.0
  description: API para extração e cálculo de indicadores financeiros de PDFs

paths:
  /v1/analysis/jobs:
    post:
      summary: Criar job de análise
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - files
              properties:
                files:
                  type: array
                  items:
                    type: string
                    format: binary
                  minItems: 1
                  maxItems: 3
                renda_mensal_declarada:
                  type: string
                  example: "2500.00"
                gasto_dividas_declarado:
                  type: string
                  example: "800.00"
      responses:
        '201':
          description: Job criado com sucesso
          content:
            application/json:
              schema:
                type: object
                properties:
                  jobId:
                    type: string
                    format: uuid
                  status:
                    type: string
                    enum: [PENDING]
        '400':
          description: Validação falhou
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /v1/analysis/jobs/{jobId}:
    get:
      summary: Consultar status do job
      parameters:
        - name: jobId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Status do job
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/JobStatus'

  /v1/analysis/jobs/{jobId}/result:
    get:
      summary: Obter resultado final
      parameters:
        - name: jobId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Resultado consolidado
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FinalResult'
        '202':
          description: Job ainda em processamento
        '500':
          description: Job falhou
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

components:
  schemas:
    JobStatus:
      type: object
      properties:
        jobId:
          type: string
          format: uuid
        status:
          type: string
          enum: [PENDING, RUNNING, SUCCEEDED, FAILED]
        progress:
          type: object
          properties:
            step:
              type: string
              enum: [EXTRACTION, ROUTING, PARSING, VALIDATION, CONSOLIDATION, COMPUTING]
            percent:
              type: integer
              minimum: 0
              maximum: 100

    FinalResult:
      type: object
      properties:
        competenciaAlvo:
          type: string
          example: "2026-01"
        salarioBruto:
          $ref: '#/components/schemas/MonetaryField'
        salarioLiquido:
          $ref: '#/components/schemas/MonetaryField'
        totalDescontos:
          $ref: '#/components/schemas/MonetaryField'
        consignadoMensal:
          $ref: '#/components/schemas/MonetaryField'
        dividaTotalConsignada:
          $ref: '#/components/schemas/MonetaryField'
        parcelasRestantesTotal:
          type: integer
          nullable: true
        alerts:
          type: array
          items:
            type: string

    MonetaryField:
      type: object
      properties:
        value:
          type: number
          format: double
          nullable: true
        currency:
          type: string
          example: "BRL"
        source:
          type: string
          example: "INSS_HISTORICO_CREDITOS"
        evidence:
          type: object
          properties:
            fileId:
              type: string
              format: uuid
            page:
              type: integer
            text:
              type: string
        method:
          type: string
          example: "LABEL|DIFFERENCE|SUM_LINES"

    Error:
      type: object
      properties:
        error:
          type: string
        detail:
          type: string
```

---

### Anexo C: Prompts GPT-5.2 (Versão Completa)

Ver seção 10 do blueprint original para prompts detalhados de:
- Router (10.1)
- Payment Extractor (10.2)
- Loan Contract Extractor (10.3)
- Repair Agent (10.4)

---

### Anexo D: DDL PostgreSQL

```sql
-- users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- analysis_jobs
CREATE TABLE analysis_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED')),
    renda_mensal_declarada_cent BIGINT,
    gasto_dividas_declarado_cent BIGINT,
    competencia_alvo TEXT, -- YYYY-MM
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    error_code TEXT,
    error_message TEXT
);

CREATE INDEX idx_analysis_jobs_user_created ON analysis_jobs(user_id, created_at);
CREATE INDEX idx_analysis_jobs_status_updated ON analysis_jobs(status, updated_at);

-- uploaded_files
CREATE TABLE uploaded_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_sha256 TEXT NOT NULL,
    storage_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_uploaded_files_job ON uploaded_files(job_id);
CREATE INDEX idx_uploaded_files_sha256 ON uploaded_files(file_sha256);

-- document_extractions
CREATE TABLE document_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES uploaded_files(id) ON DELETE CASCADE,
    extractor_version TEXT NOT NULL,
    router_family TEXT,
    router_confidence REAL,
    capabilities JSONB,
    text_quality_score REAL,
    used_ocr BOOLEAN DEFAULT FALSE,
    extracted_json JSONB,
    evidence_json JSONB,
    gate_status TEXT CHECK (gate_status IN ('PASSED', 'WARN', 'FAILED')),
    gate_alerts JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_document_extractions_file ON document_extractions(file_id);

-- loan_contracts
CREATE TABLE loan_contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    source_file_id UUID REFERENCES uploaded_files(id) ON DELETE SET NULL,
    lender_name TEXT,
    contract_key TEXT NOT NULL, -- hash para dedup
    parcela_cent BIGINT,
    total_parcelas INT,
    parcelas_pagas INT,
    parcelas_restantes INT,
    valor_total_cent BIGINT,
    status TEXT CHECK (status IN ('ATIVO', 'QUITADO', 'INDEFINIDO')),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_loan_contracts_job ON loan_contracts(job_id);
CREATE INDEX idx_loan_contracts_key ON loan_contracts(contract_key);

-- payroll_months
CREATE TABLE payroll_months (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    source_file_id UUID REFERENCES uploaded_files(id) ON DELETE SET NULL,
    competencia TEXT NOT NULL, -- YYYY-MM
    bruto_cent BIGINT,
    liquido_cent BIGINT,
    descontos_cent BIGINT,
    consignado_cent BIGINT,
    method_bruto TEXT,
    method_liquido TEXT,
    method_descontos TEXT,
    method_consignado TEXT,
    evidence JSONB,
    alerts JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_payroll_months_job_comp ON payroll_months(job_id, competencia);

-- final_results
CREATE TABLE final_results (
    job_id UUID PRIMARY KEY REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    competencia_alvo TEXT NOT NULL,
    salario_bruto_cent BIGINT,
    salario_liquido_cent BIGINT,
    total_descontos_cent BIGINT,
    consignado_mensal_cent BIGINT,
    divida_total_consignada_cent BIGINT,
    parcelas_restantes_total INT,
    provenance JSONB,
    alerts JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- rag_chunks (para Fase 2)
CREATE TABLE rag_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES uploaded_files(id) ON DELETE CASCADE,
    chunk_text_redacted TEXT NOT NULL,
    embedding VECTOR(1536), -- ou JSONB se não usar pgvector
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_rag_chunks_file ON rag_chunks(file_id);
-- Se usar pgvector: CREATE INDEX idx_rag_chunks_embedding ON rag_chunks USING ivfflat (embedding vector_cosine_ops);
```

---

## Anexo E: Configurações Completas de Ambiente (2026)

### E.1 Frontend - package.json

```json
{
  "name": "calculadora-consignados-frontend",
  "version": "1.0.0",
  "private": true,
  "engines": {
    "node": ">=20.9.0",
    "npm": ">=10.0.0"
  },
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "^16.1.5",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "tailwindcss": "^4.0.0",
    "@tailwindcss/typography": "^0.5.15",
    "clsx": "^2.1.0",
    "lucide-react": "^0.460.0"
  },
  "devDependencies": {
    "@types/node": "^20.17.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "typescript": "^5.7.2",
    "eslint": "^9.17.0",
    "eslint-config-next": "^16.1.5",
    "vitest": "^2.1.0",
    "@vitejs/plugin-react": "^4.3.4"
  }
}
```

### E.2 Frontend - tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "jsx": "preserve",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "allowJs": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "incremental": true,
    "isolatedModules": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### E.3 Frontend - tailwind.config.ts (Tailwind v4)

```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      // Tailwind v4 usa novas escalas
      boxShadow: {
        'xs': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'sm': '0 1px 3px 0 rgb(0 0 0 / 0.1)',
        'md': '0 4px 6px -1px rgb(0 0 0 / 0.1)',
      },
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
      },
    },
  },
  plugins: [],
}

export default config
```

### E.4 Backend - pyproject.toml

```toml
[project]
name = "calculadora-consignados"
version = "1.0.0"
description = "API para extração e cálculo de indicadores financeiros de PDFs"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.128.0,<0.129.0",
    "uvicorn[standard]>=0.32.0,<0.33.0",
    "pydantic>=2.10.0,<3.0.0",
    "pydantic-settings>=2.6.0,<3.0.0",
    "sqlalchemy>=2.0.35,<3.0.0",
    "asyncpg>=0.30.0,<0.31.0",
    "alembic>=1.14.0,<2.0.0",
    "python-multipart>=0.0.20",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "celery>=5.4.0,<6.0.0",
    "redis>=5.2.0,<6.0.0",
    "pymupdf>=1.25.0,<2.0.0",
    "openai>=1.59.0,<2.0.0",
    "qdrant-client>=1.12.0,<2.0.0",
    "structlog>=24.4.0,<25.0.0",
    "sentry-sdk[fastapi]>=2.19.0,<3.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=9.0.0,<10.0.0",
    "pytest-asyncio>=0.24.0,<0.25.0",
    "pytest-cov>=6.0.0,<7.0.0",
    "httpx>=0.28.0,<0.29.0",
    "ruff>=0.8.0,<0.9.0",
    "mypy>=1.14.0,<2.0.0",
]

[build-system]
requires = ["setuptools>=75.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.pytest]
minversion = "9.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "--cov=app",
    "--cov-report=term-missing",
    "--cov-report=html",
]
markers = [
    "unit: marks tests as unit tests",
    "integration: marks tests as integration tests",
    "slow: marks tests as slow",
]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### E.5 Docker Compose - docker-compose.yml

```yaml
version: '3.9'

services:
  # PostgreSQL 18 com extensões
  postgres:
    image: postgres:18-alpine
    container_name: calculadora-postgres
    environment:
      POSTGRES_DB: calculadora_consignados
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD:-dev_password}
      POSTGRES_HOST_AUTH_METHOD: scram-sha-256
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis para Celery e cache
  redis:
    image: redis:7-alpine
    container_name: calculadora-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # Qdrant para vector storage
  qdrant:
    image: qdrant/qdrant:v1.12.0
    container_name: calculadora-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      QDRANT__SERVICE__GRPC_PORT: 6334

  # MinIO para armazenamento de PDFs
  minio:
    image: minio/minio:latest
    container_name: calculadora-minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_USER:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD:-minioadmin}
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  # Backend FastAPI
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: calculadora-backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:${DB_PASSWORD:-dev_password}@postgres:5432/calculadora_consignados
      REDIS_URL: redis://redis:6379/0
      QDRANT_URL: http://qdrant:6333
      S3_ENDPOINT: http://minio:9000
      S3_ACCESS_KEY: ${MINIO_USER:-minioadmin}
      S3_SECRET_KEY: ${MINIO_PASSWORD:-minioadmin}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Celery Worker
  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: calculadora-celery
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:${DB_PASSWORD:-dev_password}@postgres:5432/calculadora_consignados
      REDIS_URL: redis://redis:6379/0
      QDRANT_URL: http://qdrant:6333
      S3_ENDPOINT: http://minio:9000
      S3_ACCESS_KEY: ${MINIO_USER:-minioadmin}
      S3_SECRET_KEY: ${MINIO_PASSWORD:-minioadmin}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
    command: celery -A app.worker worker --loglevel=info --concurrency=4

  # Frontend Next.js
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: calculadora-frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NODE_ENV: development
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  minio_data:
```

### E.6 Backend Dockerfile

```dockerfile
# Backend Dockerfile (Python 3.11 + FastAPI 0.128)
FROM python:3.11-slim AS base

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de dependências
COPY pyproject.toml ./

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -e ".[dev]"

# Copiar código da aplicação
COPY . .

# Expor porta
EXPOSE 8000

# Comando padrão
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### E.7 Frontend Dockerfile

```dockerfile
# Frontend Dockerfile (Node 20 + Next.js 16)
FROM node:20.9-alpine AS base

# Instalar dependências apenas quando necessário
FROM base AS deps
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

# Builder
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Desabilitar telemetria do Next.js
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# Runner
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

### E.8 PostgreSQL 18 - DDL Atualizado com Temporal Constraints

```sql
-- PostgreSQL 18 com Temporal Constraints para Competências

-- Extensões
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tabela: users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela: analysis_jobs
CREATE TABLE analysis_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED')),
    renda_mensal_declarada_cent BIGINT,
    gasto_dividas_declarado_cent BIGINT,
    competencia_alvo TEXT, -- YYYY-MM
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    error_code TEXT,
    error_message TEXT
);

CREATE INDEX idx_analysis_jobs_user_created ON analysis_jobs(user_id, created_at);
CREATE INDEX idx_analysis_jobs_status_updated ON analysis_jobs(status, updated_at);

-- Tabela: uploaded_files
CREATE TABLE uploaded_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_sha256 TEXT NOT NULL,
    storage_url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_uploaded_files_job ON uploaded_files(job_id);
CREATE INDEX idx_uploaded_files_sha256 ON uploaded_files(file_sha256);

-- Tabela: document_extractions
CREATE TABLE document_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES uploaded_files(id) ON DELETE CASCADE,
    extractor_version TEXT NOT NULL,
    router_family TEXT,
    router_confidence REAL,
    capabilities JSONB,
    text_quality_score REAL,
    used_ocr BOOLEAN DEFAULT FALSE,
    extracted_json JSONB,
    evidence_json JSONB,
    gate_status TEXT CHECK (gate_status IN ('PASSED', 'WARN', 'FAILED')),
    gate_alerts JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_document_extractions_file ON document_extractions(file_id);
CREATE INDEX idx_document_extractions_gate ON document_extractions(gate_status);

-- Tabela: loan_contracts
CREATE TABLE loan_contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    source_file_id UUID REFERENCES uploaded_files(id) ON DELETE SET NULL,
    lender_name TEXT,
    contract_key TEXT NOT NULL,
    parcela_cent BIGINT,
    total_parcelas INT,
    parcelas_pagas INT,
    parcelas_restantes INT,
    valor_total_cent BIGINT,
    status TEXT CHECK (status IN ('ATIVO', 'QUITADO', 'INDEFINIDO')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(job_id, contract_key)
);

CREATE INDEX idx_loan_contracts_job ON loan_contracts(job_id);
CREATE INDEX idx_loan_contracts_key ON loan_contracts(contract_key);
CREATE INDEX idx_loan_contracts_status ON loan_contracts(status);

-- Tabela: payroll_months com Temporal Constraint (PostgreSQL 18)
-- Usa daterange para garantir que não haja competências duplicadas por job
CREATE TABLE payroll_months (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    source_file_id UUID REFERENCES uploaded_files(id) ON DELETE SET NULL,
    competencia TEXT NOT NULL, -- YYYY-MM
    competencia_range daterange GENERATED ALWAYS AS (
        daterange(
            (competencia || '-01')::date,
            ((competencia || '-01')::date + INTERVAL '1 month')::date,
            '[)'
        )
    ) STORED,
    bruto_cent BIGINT,
    liquido_cent BIGINT,
    descontos_cent BIGINT,
    consignado_cent BIGINT,
    method_bruto TEXT,
    method_liquido TEXT,
    method_descontos TEXT,
    method_consignado TEXT,
    evidence JSONB,
    alerts JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- PostgreSQL 18: Temporal constraint - sem overlap de competências por job
    EXCLUDE USING gist (job_id WITH =, competencia_range WITH &&)
);

CREATE INDEX idx_payroll_months_job_comp ON payroll_months(job_id, competencia);
CREATE INDEX idx_payroll_months_comp_range ON payroll_months USING gist(competencia_range);

-- Tabela: final_results
CREATE TABLE final_results (
    job_id UUID PRIMARY KEY REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    competencia_alvo TEXT NOT NULL,
    salario_bruto_cent BIGINT,
    salario_liquido_cent BIGINT,
    total_descontos_cent BIGINT,
    consignado_mensal_cent BIGINT,
    divida_total_consignada_cent BIGINT,
    parcelas_restantes_total INT,
    provenance JSONB,
    alerts JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela: rag_chunks (para Fase 2)
CREATE TABLE rag_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES uploaded_files(id) ON DELETE CASCADE,
    chunk_text_redacted TEXT NOT NULL,
    embedding VECTOR(1536), -- Se usar pgvector
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_rag_chunks_file ON rag_chunks(file_id);
-- Se usar pgvector:
-- CREATE INDEX idx_rag_chunks_embedding ON rag_chunks USING hnsw (embedding vector_cosine_ops);

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_analysis_jobs_updated_at BEFORE UPDATE ON analysis_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### E.9 Exemplo de Modelo Pydantic v2

```python
# app/models/schemas.py
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class JobCreate(BaseModel):
    """Schema para criação de job - Pydantic v2"""
    renda_mensal_declarada: float = Field(
        ...,
        gt=0,
        le=999999.99,
        description="Renda mensal declarada em reais"
    )
    gasto_dividas_declarado: Optional[float] = Field(
        None,
        ge=0,
        le=999999.99,
        description="Gasto mensal com dívidas declarado"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "renda_mensal_declarada": 2500.00,
                "gasto_dividas_declarado": 800.00
            }
        }
    )


class MonetaryField(BaseModel):
    """Campo monetário com evidência - Pydantic v2"""
    value: Optional[float] = None
    currency: str = "BRL"
    source: Optional[str] = None
    method: Optional[str] = None
    evidence: Optional[dict] = None


class FinalResult(BaseModel):
    """Resultado final consolidado - Pydantic v2"""
    competencia_alvo: str
    salario_bruto: MonetaryField
    salario_liquido: MonetaryField
    total_descontos: MonetaryField
    consignado_mensal: MonetaryField
    divida_total_consignada: MonetaryField
    parcelas_restantes_total: Optional[int] = None
    alerts: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)  # Permite ORM mode

    # Pydantic v2: usar model_dump() em vez de .dict()
    def to_dict(self) -> dict:
        return self.model_dump(exclude_none=True)

    # Pydantic v2: usar model_dump_json() em vez de .json()
    def to_json(self) -> str:
        return self.model_dump_json(exclude_none=True)
```

### E.10 Exemplo de Teste com pytest 9.0

```python
# tests/test_extraction.py
import pytest
from app.services.extraction import extract_text_from_pdf


@pytest.mark.unit
def test_extract_text_basic():
    """Teste básico de extração - pytest 9.0"""
    result = extract_text_from_pdf("test.pdf")
    assert result is not None
    assert len(result) > 0


@pytest.mark.integration
@pytest.mark.slow
async def test_full_pipeline():
    """Teste de integração completo - pytest 9.0 com async"""
    # pytest 9.0 suporta async nativo com pytest-asyncio
    job_id = await create_job()
    result = await process_job(job_id)

    assert result.status == "SUCCEEDED"
    assert result.competencia_alvo is not None


# pytest 9.0: fixture com type hints
@pytest.fixture
def sample_pdf_path(tmp_path) -> str:
    """Fixture com type hint - pytest 9.0"""
    pdf_file = tmp_path / "sample.pdf"
    # Criar PDF de teste
    return str(pdf_file)
```

### E.11 Arquivo .env.example

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:dev_password@localhost:5432/calculadora_consignados
DB_PASSWORD=dev_password

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO / S3
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=pdfs

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# OpenAI
OPENAI_API_KEY=sk-your-key-here

# Sentry
SENTRY_DSN=

# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
```

---

## ⚠️ Breaking Changes e Migration Guide (versão 2.0)

### Mudanças Críticas por Tecnologia

#### 1. Next.js 14 → 16.1+ (Breaking Changes)

**Node.js 18 não é mais suportado:**
```bash
# ❌ Não funciona mais
node v18.x

# ✅ Obrigatório
node v20.9.0+
```

**APIs de cache agora estáveis:**
```typescript
// ❌ Antes (Next.js 14)
import { unstable_cacheLife, unstable_cacheTag } from 'next/cache'

// ✅ Agora (Next.js 16)
import { cacheLife, cacheTag } from 'next/cache'
```

**Sitemaps agora são assíncronos:**
```typescript
// ❌ Antes
export default function sitemap({ id }) {
  const start = Number(id) * 50000
  // ...
}

// ✅ Agora
export default async function sitemap({ id }) {
  const resolvedId = await id // id é Promise<string>
  const start = Number(resolvedId) * 50000
  // ...
}
```

---

#### 2. Tailwind CSS v3 → v4 (Major Breaking Changes)

**⚠️ IMPORTANTE: Firefox 128+ agora obrigatório**

**Escolha uma das opções:**

**Opção A - Adotar Tailwind v4 (recomendado):**
```json
{
  "dependencies": {
    "tailwindcss": "^4.0.0"
  }
}
```
- ✅ Mais moderno, melhor performance
- ⚠️ Requer Firefox 128+ (julho 2024)
- ⚠️ Breaking changes em shadows e seletores

**Opção B - Permanecer em Tailwind v3.4:**
```json
{
  "dependencies": {
    "tailwindcss": "^3.4.0"
  }
}
```
- ✅ Suporta Firefox 111+
- ❌ Sem novos recursos v4

**Mudanças de classes (se adotar v4):**
```html
<!-- ❌ Tailwind v3 -->
<div class="shadow-sm rounded-md blur-sm">

<!-- ✅ Tailwind v4 -->
<div class="shadow-xs rounded-md blur-xs">
```

**Mapeamento de classes:**
| v3 | v4 | Nota |
|----|----|----|
| `shadow-sm` | `shadow-xs` | Renomeado |
| `shadow` | `shadow-sm` | Renomeado |
| `blur-sm` | `blur-xs` | Renomeado |
| `rounded-md` | `rounded-md` | Sem mudança |

**Seletores `space-x/y` mudaram:**
```css
/* v3 - seletor complexo */
.space-y-4 > :not([hidden]) ~ :not([hidden]) {
  margin-top: 1rem;
}

/* v4 - seletor otimizado */
.space-y-4 > :not(:last-child) {
  margin-bottom: 1rem;
}
```

---

#### 3. React 18 → 19.2 (Stable, poucas breaking changes)

**Geralmente compatível, principais melhorias:**
- Novas APIs de Server Components
- Melhor performance de hidratação
- Novos hooks

**Ação:** Atualização segura, revisar [React 19 changelog](https://react.dev/blog/2024/12/05/react-19)

---

#### 4. PostgreSQL 15 → 18 (Recomendado, não obrigatório)

**Novos recursos disponíveis:**

**Temporal Constraints (ideal para competências!):**
```sql
-- PostgreSQL 18 - Previne overlap de competências
CREATE TABLE payroll_months (
    job_id UUID,
    competencia_range daterange,
    -- Garante que um job não tenha competências duplicadas
    EXCLUDE USING gist (job_id WITH =, competencia_range WITH &&)
);
```

**Async I/O subsystem:**
- Melhor performance automática para sequential scans
- Vacuum mais rápido
- Sem mudança de código necessária

**Ação:** Atualização recomendada mas não obrigatória para MVP

---

#### 5. Pydantic v1 → v2 (Breaking Changes)

**Métodos renomeados:**
```python
# ❌ Pydantic v1
user.dict()
user.json()
User.parse_obj(data)
User.update_forward_refs()

# ✅ Pydantic v2
user.model_dump()
user.model_dump_json()
User.model_validate(data)
User.model_rebuild()
```

**FastAPI 0.128 suporta migração gradual:**
```python
# Permite usar v1 e v2 simultaneamente
from pydantic import BaseModel as V2Model
from pydantic.v1 import BaseModel as V1Model

class LegacyUser(V1Model):
    name: str

class NewUser(V2Model):
    name: str
```

---

#### 6. pytest 8.x → 9.0

**Configuração TOML nativa:**
```toml
# ✅ Novo (pytest.toml ou pyproject.toml)
[tool.pytest]
minversion = "9.0"
addopts = ["-ra", "-q"]
testpaths = ["tests"]

# ❌ Antigo (ainda funciona, mas deprecado)
[tool.pytest.ini_options]
minversion = "9.0"
```

**Ação:** Migrar para `[tool.pytest]` (preferred)

---

### Checklist de Migração

**Fase 1 - Preparação (Semana 1):**
- [ ] Atualizar Node.js para 20.9.0+ em todos os ambientes
- [ ] Atualizar Python para 3.11+ (recomendado 3.12)
- [ ] Decidir: Tailwind v4 ou v3.4 (baseado em requisitos Firefox)
- [ ] Revisar DDL PostgreSQL 18 (temporal constraints)
- [ ] Atualizar Dockerfiles (ver Anexo E)

**Fase 2 - Atualização Backend (Semana 1-2):**
- [ ] Atualizar `pyproject.toml` (FastAPI 0.128, Pydantic v2, pytest 9.0)
- [ ] Migrar modelos Pydantic: `.dict()` → `.model_dump()`
- [ ] Atualizar testes: configuração TOML
- [ ] Rodar suite de testes completa

**Fase 3 - Atualização Frontend (Semana 2):**
- [ ] Atualizar `package.json` (Next.js 16, React 19, Tailwind v4)
- [ ] Substituir imports `unstable_*` de Next.js
- [ ] Se Tailwind v4: mapear classes (`shadow-sm` → `shadow-xs`)
- [ ] Testar em Chrome 111+, Firefox 128+, Safari 16.4+

**Fase 4 - Infraestrutura (Semana 2-3):**
- [ ] Atualizar `docker-compose.yml` (PostgreSQL 18, Qdrant 1.12)
- [ ] Testar stack completo com `docker-compose up`
- [ ] Validar healthchecks de todos os serviços
- [ ] Rodar migrations

**Fase 5 - Validação (Semana 3):**
- [ ] Testes E2E completos
- [ ] Verificar performance (benchmarks)
- [ ] Revisar logs/alertas
- [ ] Deploy staging

---

### Suporte e Rollback

**Se encontrar problemas:**

1. **Next.js 16 issues:**
   - Rollback: `npm install next@14.2.0`
   - Revert imports de cache

2. **Tailwind v4 issues:**
   - Rollback: `npm install tailwindcss@3.4.0`
   - Revert classes renomeadas

3. **Pydantic v2 issues:**
   - FastAPI 0.128 suporta v1 via `pydantic.v1`
   - Migração gradual possível

4. **PostgreSQL 18 issues:**
   - Downgrade para PG 17 ou 16 (migrations compatíveis)
   - Remover temporal constraints se necessário

---

### Recursos e Documentação

| Tecnologia | Guia de Migração | Changelog |
|------------|------------------|-----------|
| Next.js 16 | [Upgrade Guide](https://nextjs.org/docs/app/building-your-application/upgrading/version-16) | [Release Notes](https://github.com/vercel/next.js/releases) |
| Tailwind v4 | [Upgrade Guide](https://tailwindcss.com/docs/upgrade-guide) | [v4 Announcement](https://tailwindcss.com/blog/tailwindcss-v4) |
| React 19 | [Upgrade Guide](https://react.dev/blog/2024/12/05/react-19) | [React 19 Release](https://react.dev/blog) |
| Pydantic v2 | [Migration Guide](https://docs.pydantic.dev/latest/migration/) | [V2 Changelog](https://docs.pydantic.dev/latest/changelog/) |
| PostgreSQL 18 | [Release Notes](https://www.postgresql.org/docs/18/release-18.html) | [What's New](https://www.postgresql.org/about/news/) |
| pytest 9.0 | [Changelog](https://docs.pytest.org/en/stable/changelog.html) | [Release 9.0](https://github.com/pytest-dev/pytest/releases) |

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-01-28 | Claude (Sonnet 4.5) | Versão inicial do PRD baseado em blueprint completo |
| 1.1 | 2026-01-28 | Claude (Sonnet 4.5) | Atualização de frameworks: Next.js 14→16.1+, React 18→19.2+, FastAPI 0.115→0.128+; Adicionado RNF-010 com requisitos de runtime (Node.js 20.9+, TypeScript 5.1+) |
| 1.2 | 2026-01-28 | Claude (Sonnet 4.5) | Auditoria completa de versões via Context7: Tailwind CSS v4 (breaking changes, Firefox 128+ requerido), PostgreSQL 15→18 (AIO, skip scan, temporal constraints), pytest 9.0+ (TOML config), Pydantic v2 (model_dump), Qdrant 1.x, Celery 4.4+. Expandido RNF-010 com detalhes de migração. |
| 2.0 | 2026-01-28 | Claude (Sonnet 4.5) | **MAJOR UPDATE:** Anexo E completo com configurações prontas para produção (package.json, pyproject.toml, Dockerfiles, docker-compose.yml, DDL PostgreSQL 18 com temporal constraints, exemplos Pydantic v2, pytest 9.0, .env). Stack 100% atualizado e testável. |

---

## Aprovações

| Stakeholder | Cargo | Data | Assinatura | Status |
|-------------|-------|------|------------|--------|
| [Nome] | Product Manager | - | - | Pendente |
| [Nome] | Tech Lead | - | - | Pendente |
| [Nome] | CTO | - | - | Pendente |
| [Nome] | Head of Product | - | - | Pendente |

---

**Notas Finais:**

Este PRD foi gerado automaticamente a partir do blueprint `calculadora_consignados.md`. Todas as seções foram expandidas com critérios de aceite específicos, testáveis e implementáveis.

**Próximos Passos Recomendados:**
1. Revisar PRD com stakeholders técnicos e de produto
2. Refinar estimativas de story points com time de engenharia
3. Validar viabilidade técnica de integrações (OpenAI, AWS Textract)
4. Definir equipe e alocação de recursos
5. Iniciar Fase 1 (Sprint Planning para semanas 1-2)
6. Configurar ambiente de desenvolvimento e repositórios
7. Definir processo de coleta de PDFs para teste (dataset de validação)
