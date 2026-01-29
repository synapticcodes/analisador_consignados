-- ==============================================
-- Calculadora de Consignados - Database Schema
-- PostgreSQL 18
-- ==============================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================================
-- Function: update_updated_at_column
-- ==============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ==============================================
-- Table: users
-- ==============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    password_hash TEXT,
    full_name TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==============================================
-- Table: analysis_jobs
-- ==============================================
CREATE TABLE IF NOT EXISTS analysis_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Status
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED')),

    -- Valores declarados (em centavos)
    renda_mensal_declarada_cent BIGINT,
    gasto_dividas_declarado_cent BIGINT,

    -- Competência consolidada
    competencia_alvo TEXT, -- YYYY-MM format

    -- Error tracking
    error_code TEXT,
    error_message TEXT,

    -- Metadata
    processing_time_ms INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_analysis_jobs_user_id ON analysis_jobs(user_id);
CREATE INDEX idx_analysis_jobs_status ON analysis_jobs(status);
CREATE INDEX idx_analysis_jobs_created_at ON analysis_jobs(created_at DESC);
CREATE INDEX idx_analysis_jobs_user_created ON analysis_jobs(user_id, created_at DESC);

CREATE TRIGGER update_analysis_jobs_updated_at BEFORE UPDATE ON analysis_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==============================================
-- Table: uploaded_files
-- ==============================================
CREATE TABLE IF NOT EXISTS uploaded_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,

    -- File info
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL DEFAULT 'application/pdf',
    file_size BIGINT NOT NULL,
    file_sha256 TEXT NOT NULL,

    -- Storage
    storage_url TEXT NOT NULL,
    storage_provider TEXT DEFAULT 'minio',

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_uploaded_files_job_id ON uploaded_files(job_id);
CREATE INDEX idx_uploaded_files_sha256 ON uploaded_files(file_sha256);
CREATE INDEX idx_uploaded_files_created_at ON uploaded_files(created_at DESC);

-- ==============================================
-- Table: document_extractions
-- ==============================================
CREATE TABLE IF NOT EXISTS document_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES uploaded_files(id) ON DELETE CASCADE,

    -- Versioning
    extractor_version TEXT NOT NULL DEFAULT '1.0',

    -- Router output
    router_family TEXT,
    router_confidence REAL,
    capabilities JSONB,
    competencias_detectadas JSONB,

    -- Text extraction
    text_quality_score REAL,
    used_ocr BOOLEAN DEFAULT FALSE,
    extraction_method TEXT, -- 'native', 'ocr'

    -- Extractor output
    extracted_json JSONB,
    evidence_json JSONB,

    -- Evidence Gate
    gate_status TEXT CHECK (gate_status IN ('PASSED', 'WARN', 'FAILED')),
    gate_alerts JSONB,

    -- Metadata
    processing_time_ms INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_document_extractions_file_id ON document_extractions(file_id);
CREATE INDEX idx_document_extractions_gate_status ON document_extractions(gate_status);
CREATE INDEX idx_document_extractions_router_family ON document_extractions(router_family);

-- ==============================================
-- Table: loan_contracts
-- ==============================================
CREATE TABLE IF NOT EXISTS loan_contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    source_file_id UUID REFERENCES uploaded_files(id) ON DELETE SET NULL,

    -- Contract info
    lender_name TEXT,
    contract_id TEXT,
    contract_key TEXT NOT NULL, -- Hash for deduplication

    -- Valores (em centavos)
    parcela_cent BIGINT,
    total_parcelas INTEGER,
    parcelas_pagas INTEGER,
    parcelas_restantes INTEGER,
    valor_total_cent BIGINT,

    -- Status
    status TEXT CHECK (status IN ('ATIVO', 'QUITADO', 'INDEFINIDO')) DEFAULT 'ATIVO',

    -- Evidence
    evidence JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_loan_contracts_job_id ON loan_contracts(job_id);
CREATE INDEX idx_loan_contracts_contract_key ON loan_contracts(contract_key);
CREATE UNIQUE INDEX idx_loan_contracts_unique_key ON loan_contracts(job_id, contract_key);

-- ==============================================
-- Table: payroll_months
-- ==============================================
CREATE TABLE IF NOT EXISTS payroll_months (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    source_file_id UUID REFERENCES uploaded_files(id) ON DELETE SET NULL,

    -- Competência
    competencia TEXT NOT NULL, -- YYYY-MM format

    -- Valores consolidados (em centavos)
    bruto_cent BIGINT,
    liquido_cent BIGINT,
    descontos_cent BIGINT,
    consignado_cent BIGINT,

    -- Métodos utilizados
    method_bruto TEXT,
    method_liquido TEXT,
    method_descontos TEXT,
    method_consignado TEXT,

    -- Evidence & provenance
    evidence JSONB,
    provenance JSONB,

    -- Linhas de consignado (array de objetos)
    consignado_lines JSONB,

    -- Alertas
    alerts JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_payroll_months_job_id ON payroll_months(job_id);
CREATE INDEX idx_payroll_months_competencia ON payroll_months(competencia);
CREATE INDEX idx_payroll_months_job_comp ON payroll_months(job_id, competencia);

-- ==============================================
-- Table: final_results
-- ==============================================
CREATE TABLE IF NOT EXISTS final_results (
    job_id UUID PRIMARY KEY REFERENCES analysis_jobs(id) ON DELETE CASCADE,

    -- Competência alvo
    competencia_alvo TEXT NOT NULL,

    -- 6 Outputs principais (em centavos)
    salario_bruto_cent BIGINT,
    salario_liquido_cent BIGINT,
    total_descontos_cent BIGINT,
    consignado_mensal_cent BIGINT,
    divida_total_consignada_cent BIGINT,
    parcelas_restantes_total INTEGER,

    -- Provenance (rastreabilidade)
    provenance JSONB,

    -- Alertas consolidados
    alerts JSONB,

    -- Metadata
    calculation_methods JSONB,
    confidence_scores JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================
-- Table: rag_chunks (Para Fase 2)
-- ==============================================
CREATE TABLE IF NOT EXISTS rag_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES uploaded_files(id) ON DELETE CASCADE,

    -- Texto redigido (sem PII)
    chunk_text_redacted TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_size INTEGER NOT NULL,

    -- Embedding (usando JSONB se não tiver pgvector)
    embedding JSONB,
    -- Se usar pgvector: embedding VECTOR(1536),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_rag_chunks_file_id ON rag_chunks(file_id);
-- Se usar pgvector:
-- CREATE INDEX idx_rag_chunks_embedding ON rag_chunks USING ivfflat (embedding vector_cosine_ops);

-- ==============================================
-- Table: repair_proposals (Para Fase 3)
-- ==============================================
CREATE TABLE IF NOT EXISTS repair_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    file_id UUID REFERENCES uploaded_files(id) ON DELETE CASCADE,

    -- Proposal
    proposal_type TEXT, -- 'NEW_FAMILY', 'ANCHOR_IMPROVEMENT', 'PROMPT_PATCH'
    proposal_content JSONB NOT NULL,

    -- Testing
    tested_at TIMESTAMP WITH TIME ZONE,
    test_results JSONB,
    test_pass_rate REAL,

    -- Status
    status TEXT CHECK (status IN ('PENDING', 'TESTED', 'APPROVED', 'REJECTED', 'DEPLOYED')),

    -- Metadata
    similar_cases JSONB, -- IDs de casos similares do RAG
    created_by TEXT DEFAULT 'repair_agent',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deployed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_repair_proposals_status ON repair_proposals(status);
CREATE INDEX idx_repair_proposals_created_at ON repair_proposals(created_at DESC);

-- ==============================================
-- View: jobs_with_files
-- ==============================================
CREATE OR REPLACE VIEW jobs_with_files AS
SELECT
    j.id as job_id,
    j.status,
    j.competencia_alvo,
    j.created_at,
    COUNT(f.id) as file_count,
    SUM(f.file_size) as total_file_size
FROM analysis_jobs j
LEFT JOIN uploaded_files f ON j.id = f.job_id
GROUP BY j.id;

-- ==============================================
-- View: jobs_summary
-- ==============================================
CREATE OR REPLACE VIEW jobs_summary AS
SELECT
    j.id as job_id,
    j.user_id,
    j.status,
    j.competencia_alvo,
    j.created_at,
    j.completed_at,
    COUNT(DISTINCT f.id) as file_count,
    COUNT(DISTINCT de.id) as extraction_count,
    COUNT(DISTINCT lc.id) as contract_count,
    fr.salario_bruto_cent,
    fr.salario_liquido_cent,
    fr.consignado_mensal_cent,
    fr.divida_total_consignada_cent
FROM analysis_jobs j
LEFT JOIN uploaded_files f ON j.id = f.job_id
LEFT JOIN document_extractions de ON f.id = de.file_id
LEFT JOIN loan_contracts lc ON j.id = lc.job_id
LEFT JOIN final_results fr ON j.id = fr.job_id
GROUP BY j.id, fr.salario_bruto_cent, fr.salario_liquido_cent,
         fr.consignado_mensal_cent, fr.divida_total_consignada_cent;

-- ==============================================
-- Comments (Documentação)
-- ==============================================
COMMENT ON TABLE users IS 'Usuários do sistema';
COMMENT ON TABLE analysis_jobs IS 'Jobs de análise de PDFs';
COMMENT ON TABLE uploaded_files IS 'Arquivos PDF enviados';
COMMENT ON TABLE document_extractions IS 'Extrações de dados dos documentos';
COMMENT ON TABLE loan_contracts IS 'Contratos de empréstimo extraídos';
COMMENT ON TABLE payroll_months IS 'Dados de folha de pagamento por competência';
COMMENT ON TABLE final_results IS 'Resultados consolidados finais';
COMMENT ON TABLE rag_chunks IS 'Chunks de texto para RAG (auto-aprimoramento)';
COMMENT ON TABLE repair_proposals IS 'Propostas de melhoria do Repair Agent';

COMMENT ON COLUMN analysis_jobs.renda_mensal_declarada_cent IS 'Renda mensal declarada em centavos';
COMMENT ON COLUMN analysis_jobs.gasto_dividas_declarado_cent IS 'Gasto com dívidas declarado em centavos';
COMMENT ON COLUMN final_results.salario_bruto_cent IS 'Salário bruto em centavos (BIGINT para precisão)';
COMMENT ON COLUMN final_results.salario_liquido_cent IS 'Salário líquido em centavos';
