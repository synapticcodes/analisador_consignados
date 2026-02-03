# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Adicionado
- Novas métricas determinísticas: Dívida Mensal (90% dos descontos), Dívida Mensal Reduzida (25% da dívida mensal) e Dívida Total Reduzida (25% da dívida total consignada)
- Persistência das novas métricas em `final_results` via migrations Alembic
- Métodos de cálculo para percentuais no Compute Engine
- Infraestrutura completa inicial do projeto
- Backend FastAPI 0.128.0 com Python 3.11+
- Frontend Next.js 16.1.5 com React 19.2
- Docker Compose com PostgreSQL 18, Redis 7, Qdrant 1.12+, MinIO
- Estrutura de banco de dados completa (DDL)
- Configurações de desenvolvimento e produção
- Documentação completa (README, CONTRIBUTING)
- Makefile com comandos úteis
- Configuração de testes (pytest, Vitest)

### Modificado
- `GET /v1/analysis/jobs/{jobId}/result` agora retorna 9 outputs (incluindo as novas métricas)
- UI de resultados atualizada para exibir 7 outputs principais

### Descontinuado
- Métricas `consignado_mensal` e `parcelas_restantes_total` marcadas como legacy na UI

### Removido
- Cards de `Consignado Mensal` e `Parcelas Restantes` da tela de resultados

## [1.0.0] - 2026-01-28

### Adicionado
- Setup inicial do projeto
- Estrutura de pastas para backend e frontend
- Configurações de ambiente (.env.example)
- Dockerfiles otimizados multi-stage
- Alembic para migrations
- Linting e formatação (Black, Ruff, Prettier, ESLint)
- Health checks para todos os serviços

---

## Tipos de Mudanças

- `Adicionado` para novas funcionalidades
- `Modificado` para mudanças em funcionalidades existentes
- `Descontinuado` para funcionalidades que serão removidas
- `Removido` para funcionalidades removidas
- `Corrigido` para correções de bugs
- `Segurança` para vulnerabilidades corrigidas
