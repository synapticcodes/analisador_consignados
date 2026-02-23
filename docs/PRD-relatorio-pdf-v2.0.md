# PRD — Evolução do Relatório PDF

**Diagnóstico Financeiro v2 — Calculadora de Consignados**

| Campo | Valor |
|-------|-------|
| **Versão** | 2.0 |
| **Data** | 05/02/2026 |
| **Status** | Proposta para Revisão |
| **Autor** | Claude (revisão técnica) |
| **Stack** | FastAPI + Next.js 16 + PostgreSQL 18 |

---

## Índice

1. [Sumário Executivo](#1-sumário-executivo)
2. [Estado Atual do Sistema](#2-estado-atual-do-sistema)
3. [Mapeamento: Documentos Reais vs. Dados Disponíveis](#3-mapeamento-documentos-reais-vs-dados-disponíveis)
4. [Estratégia de Dados: 3 Camadas](#4-estratégia-de-dados-3-camadas)
5. [Fase 1 — Surfacear Dados Existentes (Quick Wins)](#5-fase-1--surfacear-dados-existentes-quick-wins)
6. [Fase 2 — Enriquecer Extração (Novos Dados)](#6-fase-2--enriquecer-extração-novos-dados)
7. [Fase 3 — Seções Avançadas do Relatório](#7-fase-3--seções-avançadas-do-relatório)
8. [Especificações Técnicas](#8-especificações-técnicas)
9. [Cronograma e Dependências](#9-cronograma-e-dependências)
10. [Critérios de Aceitação](#10-critérios-de-aceitação)
11. [Roadmap de Evolução de Dados](#11-roadmap-de-evolução-de-dados)
12. [Questões em Aberto](#12-questões-em-aberto)

---

## 1. Sumário Executivo

Este PRD detalha a evolução do relatório PDF da Calculadora de Consignados, de um documento de 1 página com 7 números agregados para um diagnóstico financeiro multi-página que exibe dados detalhados por contrato, dados de margem INSS e linhas individuais do contracheque.

### 1.1 Problema

O sistema atual extrai dados ricos via OCR/LLM (nome do banco, taxa de juros, CET, parcelas por contrato, margem INSS por modalidade), mas o PDF exportado mostra apenas 7 números totalizados num layout "antes e depois". O lead recebe um documento genérico que não diferencia sua situação de nenhum outro.

### 1.2 Objetivo

Surfacear no relatório PDF todos os dados que o backend já extrai e armazena, adicionando: tabela de contratos por banco com taxa e CET, breakdown das linhas de consignado do contracheque, dados de margem INSS (emprestimo/RMC/RCC), custo real da dívida, e simulação de economia por portabilidade.

### 1.3 Usuário-alvo

Pessoa física endividada (servidor público ou beneficiário INSS) que chega via WhatsApp/formulário, envia contracheque e extrato de consignado, e recebe o relatório como ferramenta de conversão para contratação de consultoria.

### 1.4 Métricas de Sucesso

- Taxa de conversão lead → consultoria: aumento de 15% após Fase 1
- Tempo de export do PDF: < 10 segundos para documento multi-página
- Dados exibidos por relatório: de 7 campos para 25+ campos personalizados
- Satisfação do lead: "O relatório mostra exatamente minha situação"

---

## 2. Estado Atual do Sistema

### 2.1 Fluxo de Dados

Upload PDF → Router (classifica documento) → Extractors (LLM + regex) → Evidence Gate (validação) → Consolidator (merge fontes) → Compute Engine (cálculos) → FinalResult + Offers → PDF Export

### 2.2 O Que o Backend Extrai Hoje

O backend já extrai e armazena os seguintes dados por contrato no model LoanContract:

| Campo | Model/Campo | Tipo | Exibido no PDF? |
|-------|-------------|------|-----------------|
| Nome do banco | lender_name | str | **NAO** |
| Nº do contrato | contract_id | str | **NAO** |
| Parcela mensal | parcela_cent | int (centavos) | **SÓ SOMA** |
| Total de parcelas | total_parcelas | int | **NAO** |
| Parcelas pagas | parcelas_pagas | int | **NAO** |
| Parcelas restantes | parcelas_restantes | int | **SÓ SOMA** |
| Valor total | valor_total_cent | int (centavos) | **SÓ SOMA** |
| Taxa de juros | taxa_juros | str | **NAO** |
| Status | status | enum | **NAO** |
| Evidência | evidence | JSONB | **NAO** |

Além disso, o PayrollMonth armazena consignado_lines (JSONB) com descrição do banco, rubrica e valor por linha. O extrato INSS contém margem por modalidade (empréstimo, RMC, RCC), CET e IOF — dados que são parcialmente parseados mas não são armazenados em campos estruturados.

### 2.3 O Que o PDF Mostra Hoje

Apenas 7 números agregados em 1 página A4 (1240×1754px) no layout "Antes e Depois":

| # | Campo | Fórmula | Formato |
|---|-------|---------|---------|
| 1 | Salário bruto | Extraído do contracheque | R$ X.XXX,XX |
| 2 | Salário líquido | Extraído do contracheque | R$ X.XXX,XX |
| 3 | Total de descontos | Bruto - Líquido | R$ X.XXX,XX |
| 4 | Dívida mensal | Descontos × 90% | R$ X.XXX,XX |
| 5 | Dívida mensal reduzida | Dívida × 25% | R$ X.XXX,XX |
| 6 | Dívida total consignada | SUM(contratos.valor_total) | R$ XX.XXX,XX |
| 7 | Dívida total reduzida | Total × 25% | R$ XX.XXX,XX |

**Problema central:** o backend extrai ~20 campos por contrato, mas o PDF mostra apenas 7 totais. Os dados mais valiosos para o lead (qual banco, qual taxa, quanto de juros) existem no banco de dados mas nunca chegam ao relatório.

### 2.4 Gap: Dados Disponíveis vs. Exibidos

Dados que existem no backend mas NÃO aparecem no PDF:

- Tabela de contratos individuais (banco, parcela, prazo, saldo, taxa)
- Linhas do contracheque com banco + rubrica + valor
- Margem INSS por modalidade (empréstimo, RMC, RCC)
- Base de cálculo e máximo de comprometimento INSS
- CET mensal/anual e IOF do contrato ativo
- Valor emprestado vs. valor a pagar (custo real)
- Histórico de refinanciamentos (contratos encerrados)
- Ofertas (existem na página web mas não entram no PDF)

---

## 3. Mapeamento: Documentos Reais vs. Dados Disponíveis

Análise realizada com dois documentos reais de leads: contracheque SIGEPE (servidor federal UFRGS) e Histórico de Empréstimo Consignado INSS (12 páginas, pensão por morte).

### 3.1 Dados Extraídos do Contracheque

| Dado | Valor (exemplo) | Uso no relatório |
|------|-----------------|------------------|
| Salário bruto | R$ 15.065,86 | ✅ Exibido |
| Salário líquido | R$ 6.396,88 | ✅ Exibido |
| Total descontos | R$ 8.668,98 | ✅ Exibido |
| 16 linhas de empréstimo | R$ 4.641,30 total | ❌ SÓ soma — detalhe não exibido |
| 8 bancos diferentes | BRB, PRB, PAN, SAF, etc. | ❌ Não exibido |
| Rubrica por empréstimo | 086, 095, 051, etc. | ❌ Não exibido |
| Cartão crédito consignado | R$ 28,45 (PAN) | ❌ Não exibido |

### 3.2 Dados Extraídos do Extrato INSS (12 págs)

| Dado | Valor (exemplo) | Status de extração |
|------|-----------------|-------------------|
| Base de cálculo benefício | R$ 1.621,00 | 🟡 Parcialmente extraído |
| Máx. comprometimento | R$ 729,45 | 🟡 Parcialmente extraído |
| Total comprometido | R$ 611,35 | 🟡 Parcialmente extraído |
| Margem empréstimo | R$ 37,05 disponível | 🔴 Não armazenado em campo |
| Margem RMC | R$ 0,00 disponível | 🔴 Não armazenado em campo |
| Margem RCC | R$ 81,05 disponível | 🔴 Não armazenado em campo |
| Contrato ativo: parcela | R$ 530,30 | ✅ Extraído (LoanContract) |
| Contrato ativo: taxa juros | 1,80% a.m. / 23,87% a.a. | 🟡 Extraído mas inconsistente |
| Contrato ativo: CET | 1,81% mensal / 24,14% anual | 🔴 Não capturado |
| Contrato ativo: IOF | R$ 7,45 | 🔴 Não capturado |
| Valor emprestado | R$ 5.593,83 | 🔴 Não armazenado (campo ausente) |
| 20+ contratos encerrados | Desde 2005 | 🔴 Não capturados |
| Cartão RMC ativo | Daycoval, limite R$ 1.100 | 🔴 Não capturado |
| Histórico descontos cartão | 60+ parcelas (2016-2021) | 🔴 Não capturado |

---

## 4. Estratégia de Dados: 3 Camadas

**Premissa crítica:** as únicas fontes de dados reais são o contracheque e o extrato de consignado enviados pelo lead. As fontes listadas no escopo original (Serasa, Boa Vista, SPC, Quod, Open Finance, Registrato/SCR) não são consultadas. Todo o relatório deve ser construído honestamente sobre os dados que existem.

### 4.1 Camada 1 — CONFIRMADO (dados reais dos documentos)

Métricas calculáveis com precisão a partir dos documentos enviados:

| # | Métrica | Fonte real | Exemplo |
|---|---------|-----------|---------|
| 1 | **Salário bruto** | Contracheque | R$ 15.065,86 |
| 2 | **Salário líquido** | Contracheque | R$ 6.396,88 |
| 3 | **Margem consignável** | Contracheque (35% bruto - consignados) ou INSS (campo oficial) | R$ 37,05 |
| 4 | **Comprometimento mensal** | Parcelas ÷ líquido | 72,5% (R$ 4.641 de R$ 6.396) |
| 5 | **Taxa de juros** | Extrato INSS (campo da tabela) | 1,80% a.m. |
| 6 | **CET** | Extrato INSS (campo da tabela) | 1,81% a.m. / 24,14% a.a. |
| 7 | **Custo total projetado** | Parcela × prazo vs. saldo devedor | Pagará R$ 6.363 para quitar R$ 5.265 |
| 8 | **Economia potencial** | Simulação com taxa de mercado | Parcela pode cair R$ 230/mês |

### 4.2 Camada 2 — INDICAÇÃO (inferências com ressalva)

Conclusões razoáveis com base na Camada 1, sempre com disclaimer:

- Risco financeiro: se comprometimento > 70% e margem = 0, risco é alto
- Tendência: projeção simplificada das parcelas restantes
- Posição relativa: comparação com médias públicas (BC/IBGE)

**Formato obrigatório:** "Com base nos documentos analisados, indica-se que..." — nunca como CONFIRMADO.

### 4.3 Camada 3 — NÃO DISPONÍVEL (gancho de conversão)

Métricas que requerem fontes externas. Usar como argumento de venda:

- Score de crédito real → "Na consultoria, fazemos a consulta real do seu score"
- Negativações e protestos → "Descubra exatamente onde está negativado"
- Mapa completo de dívidas (Registrato) → "Veja todas as suas dívidas em todos os bancos"
- Cheque especial e cartão (Open Finance) → "Entenda quanto perde com juros ocultos"

**Ação imediata:** remover todas as referências a fontes não consultadas (Serasa, Boa Vista, SPC, Quod, Open Finance, Registrato/SCR). Substituir por "Dados obtidos de: Documentos enviados".

---

## 5. Fase 1 — Surfacear Dados Existentes (Quick Wins)

Usar dados que o backend já extrai e armazena, com mínimas mudanças na extração. Foco em mudanças no schema da API + frontend.

### 5.1 Requisito: Tabela de Contratos por Banco

**Problema:** O lead não sabe quais bancos têm empréstimos nem quanto paga em cada um.

**Solução:** Exibir no PDF uma tabela com todos os LoanContract ativos, mostrando: banco (lender_name), parcela mensal, parcelas restantes, saldo devedor (valor_total), taxa de juros e status.

**Fonte dos dados:** Model LoanContract (já persistido no banco). Necessita apenas adicionar ao schema de resposta da API e ao componente ResultSnapshot.

#### Alterações técnicas

- `backend/app/schemas/final_result.py`: Novo sub-schema LoanContractDetail (lender_name, parcela_brl, parcelas_restantes, valor_total_brl, taxa_juros, status)
- `backend/app/api/v1/analysis.py`: Query LoanContract por job_id no endpoint GET /jobs/{id}/result
- `frontend/src/types/api.ts`: Nova interface LoanContractDetail
- `frontend/src/components/pdf-sections/contracts-table.tsx`: Novo componente com tabela formatada
- `frontend/src/components/result-snapshot.tsx`: Adicionar seção de contratos na página 2

### 5.2 Requisito: Breakdown das Linhas de Consignado

**Problema:** O contracheque mostra 16+ linhas de empréstimo com banco e valor, mas o PDF só mostra a soma total.

**Solução:** Quando não há LoanContract detalhado (ex: só contracheque, sem extrato INSS), exibir as linhas individuais do consignado do contracheque com descrição (banco + tipo) e valor.

**Fonte dos dados:** PayrollMonth.consignado_lines (JSONB, já armazenado). Cada linha tem: descricao, rubrica, valor_cent.

#### Alterações técnicas

- `backend/app/schemas/final_result.py`: Novo sub-schema ConsignadoLineDetail (descricao, rubrica, valor_brl)
- `backend/app/api/v1/analysis.py`: Query PayrollMonth por job_id, extrair consignado_lines do JSONB
- `frontend/src/components/pdf-sections/consignado-breakdown.tsx`: Novo componente

### 5.3 Requisito: Dados de Margem INSS

**Problema:** O extrato INSS informa a margem oficial por modalidade (empréstimo, RMC, RCC), mas essa informação não aparece no relatório.

**Solução:** Quando o documento é um extrato INSS (router_family = INSS_EXTRATO_CONSIGNADO), extrair e exibir: base de cálculo, máximo comprometimento permitido, total comprometido, margem disponível por modalidade.

#### Alterações técnicas

- `backend/app/models/inss_margin.py`: NOVO model INSSMargin (base_calculo_cent, max_comprometimento_cent, total_comprometido_cent, margem_emprestimo_cent, margem_rmc_cent, margem_rcc_cent, cet_mensal, cet_anual)
- `backend/app/services/extractors.py`: Novo método _extract_inss_margin_data() com regex para seção "Margem para Empréstimo/Cartão e Resumo Financeiro" e tabela "VALORES POR MODALIDADE"
- `backend/alembic/versions/xxx.py`: Migration para nova tabela inss_margins
- `backend/app/schemas/final_result.py`: Novo sub-schema INSSMarginDetail
- `frontend/src/components/pdf-sections/inss-margin-section.tsx`: Novo componente

### 5.4 Requisito: Ofertas no PDF

**Problema:** As ofertas (PRINCIPAL, REDUZIDA, SUPER) aparecem na página web mas não são incluídas no PDF exportado.

**Solução:** Adicionar seção de ofertas ao PDF com destaque visual.

#### Alterações técnicas

- `frontend/src/components/pdf-sections/offers-section.tsx`: Novo componente que renderiza as ofertas no formato PDF
- `frontend/src/components/result-snapshot.tsx`: Incluir OffersSection na página 3

### 5.5 Requisito: Redesign Multi-Página do PDF

**Problema:** O PDF atual é 1 página fixa (1240×1754px), gerada como imagem PNG embutida em jsPDF. Não suporta conteúdo adicional.

**Solução:** Redesign do ResultSnapshot para estrutura multi-página com page breaks CSS. Cada seção é renderizada como div com altura A4, convertida individualmente para PNG e adicionada como página no jsPDF.

#### Estrutura proposta do PDF

**Página 1 — Retrato Financeiro:** Header com nome/data, bloco salário (bruto/líquido/descontos), barra de comprometimento, destaque de economia mensal/anual.

**Página 2 — Detalhamento:** Tabela de contratos OU linhas de consignado (o que estiver disponível), com totalização.

**Página 3 — Margem e Ofertas:** Dados de margem INSS (se disponível) + ofertas de renegociação.

**Página 4 — Metodologia e CTA:** Como os dados foram obtidos, disclaimer legal, "O que ainda não sabemos sobre você" (Camada 3), call-to-action para consultoria.

#### Alterações técnicas

- `frontend/src/components/result-snapshot.tsx`: Reescrever com divs de altura fixa A4 (794×1123px) por página
- `frontend/src/app/jobs/[id]/result/page.tsx`: Atualizar handleExportPdf() para renderizar cada página separadamente e compor no jsPDF
- `frontend/src/components/pdf-sections/`: 5 novos componentes (cover-summary, contracts-table, consignado-breakdown, inss-margin-section, methodology-footer)

---

## 6. Fase 2 — Enriquecer Extração (Novos Dados)

Expandir os extractors para capturar dados que existem nos documentos mas não são extraídos hoje.

### 6.1 Extrair CET e IOF do Extrato INSS

A tabela "CONTRATOS ATIVOS E SUSPENSOS" do extrato INSS contém: CET MENSAL, CET ANUAL, TAXA JUROS MENSAL, TAXA JUROS ANUAL, IOF. Esses campos devem ser capturados.

#### Alterações técnicas

- `backend/app/models/loan_contract.py`: Adicionar colunas cet_mensal (str), cet_anual (str), iof_cent (int), valor_emprestado_cent (int)
- `backend/app/services/extractors.py`: Atualizar regex em _extract_inss_extrato_contracts_deterministic() para capturar CET MENSAL, CET ANUAL, IOF, EMPRESTADO da tabela INSS
- `backend/app/services/extractors.py`: Atualizar LoanContractResult com campos cet_mensal, cet_anual, iof, valor_emprestado
- Migration: ALTER TABLE loan_contracts ADD COLUMN cet_mensal, cet_anual, iof_cent, valor_emprestado_cent

### 6.2 Extrair Histórico de Contratos Encerrados

A seção "CONTRATOS EXCLUÍDOS E ENCERRADOS" do extrato INSS contém 20+ contratos históricos com: banco, data, parcela, valor emprestado, motivo de exclusão (refinanciamento, quitação, troca de titularidade). Esse histórico revela padrões de rolagem e bola de neve.

#### Alterações técnicas

- `backend/app/models/historical_contract.py`: NOVO model HistoricalContract (lender_name, contract_id, data_contratacao, data_quitacao, parcela_cent, valor_emprestado_cent, motivo_encerramento)
- `backend/app/services/extractors.py`: Novo método _extract_inss_historical_contracts() com regex para tabela de encerrados
- Migration: CREATE TABLE historical_contracts

### 6.3 Calcular Custo Real por Contrato

Para cada LoanContract com valor_emprestado_cent e parcela_cent × parcelas: custo_juros = total_a_pagar - valor_emprestado. Essa métrica é a mais impactante para conversão ("Você vai pagar R$ 6.363 para quitar R$ 5.265 — R$ 1.098 só em juros").

#### Alterações técnicas

- `backend/app/services/compute_engine.py`: Novo cálculo custo_juros_cent por contrato e agregado
- `backend/app/schemas/final_result.py`: Adicionar custo_juros_total_brl e custo_juros_por_contrato[] ao response

### 6.4 Simulador de Economia por Portabilidade

Calcular cenário hipotético: se cada contrato fosse portado para taxa de mercado referência (configurável). Retorna: nova parcela estimada, economia mensal e total. Disclaimer obrigatório.

#### Alterações técnicas

- `backend/app/services/savings_simulator.py`: NOVO serviço SavingsSimulator com método simulate_refinancing()
- Parâmetro configurável: taxa_referencia_mensal (default: 1,50% para consignado público)
- Retorno: SavingsSimulation (parcela_atual, parcela_nova, economia_mensal, economia_total, disclaimer)

### 6.5 Extrair Detalhes do Cartão RMC/RCC

Seção "CARTÃO DE CRÉDITO" do extrato INSS. Extrair: contratos ativos de RMC (banco, limite, reservado) e histórico de descontos.

#### Alterações técnicas

- `backend/app/services/extractors.py`: Novo método _extract_inss_rmc_details() para seção de cartão
- Armazenar no model INSSMargin (campos rmc_banco, rmc_limite_cent, rmc_reservado_cent)

---

## 7. Fase 3 — Seções Avançadas do Relatório

### 7.1 Mapa de Dívidas Visual

Tabela consolidada com todas as dívidas (contratos + linhas contracheque), agrupadas por banco, com barra de comprometimento visual e indicador de taxa (verde se abaixo do mercado, vermelho se acima).

### 7.2 Análise de Custo Total

Seção destacada: "Total emprestado: R$ X | Total que vai pagar: R$ Y | Juros: R$ Z (W%)". Agregado e por contrato. É a métrica de conversão mais poderosa.

### 7.3 Seção "O Que Ainda Não Sabemos" (CTA)

Lista de 3-4 métricas que requerem análise completa (Camada 3), formatada como gancho: "Quer saber seu score real e todas as suas dívidas? Na consultoria completa, revelamos o quadro inteiro." Com QR code ou link para agendamento.

### 7.4 Histórico de Refinanciamentos

Timeline visual mostrando os refinanciamentos ao longo dos anos (dados da Fase 2.2). Responde: "Há quanto tempo você depende de consignado?" e "Quantas vezes refinanciou?"

---

## 8. Especificações Técnicas

### 8.1 Arquivos a Modificar

| Arquivo | Fase | Tipo |
|---------|------|------|
| backend/app/schemas/final_result.py | 1 | Modificar |
| backend/app/api/v1/analysis.py | 1 | Modificar |
| backend/app/services/extractors.py | 1+2 | Modificar |
| backend/app/models/loan_contract.py | 2 | Modificar |
| backend/app/models/\_\_init\_\_.py | 1 | Modificar |
| backend/app/services/compute_engine.py | 2 | Modificar |
| backend/app/services/consolidator.py | 1 | Modificar |
| frontend/src/types/api.ts | 1 | Modificar |
| frontend/src/components/result-snapshot.tsx | 1 | **Reescrever** |
| frontend/src/app/jobs/[id]/result/page.tsx | 1 | Modificar |

### 8.2 Arquivos a Criar

| Arquivo | Fase | Propósito |
|---------|------|-----------|
| backend/app/models/inss_margin.py | 1 | Model margem INSS |
| backend/alembic/versions/xxx_report_v2.py | 1 | Migration |
| backend/app/models/historical_contract.py | 2 | Model histórico |
| backend/app/services/savings_simulator.py | 2 | Simulador economia |
| frontend/src/components/pdf-sections/cover-summary.tsx | 1 | Capa PDF |
| frontend/src/components/pdf-sections/contracts-table.tsx | 1 | Tabela contratos |
| frontend/src/components/pdf-sections/consignado-breakdown.tsx | 1 | Linhas consignado |
| frontend/src/components/pdf-sections/inss-margin-section.tsx | 1 | Margem INSS |
| frontend/src/components/pdf-sections/offers-section.tsx | 1 | Ofertas no PDF |
| frontend/src/components/pdf-sections/methodology-footer.tsx | 1 | Rodapé + CTA |

### 8.3 Schema do Banco de Dados

#### Nova tabela: inss_margins

| Coluna | Tipo | Nullable | Descrição |
|--------|------|----------|-----------|
| **id** | UUID | Não | PK |
| **job_id** | UUID | Não | FK analysis_jobs (UNIQUE) |
| **source_file_id** | UUID | Sim | FK uploaded_files |
| **base_calculo_cent** | BIGINT | Sim | Base de cálculo do benefício |
| **max_comprometimento_cent** | BIGINT | Sim | Máximo permitido |
| **total_comprometido_cent** | BIGINT | Sim | Total já comprometido |
| **margem_emprestimo_cent** | BIGINT | Sim | Margem disponível empréstimos |
| **margem_rmc_cent** | BIGINT | Sim | Margem disponível RMC |
| **margem_rcc_cent** | BIGINT | Sim | Margem disponível RCC |
| **cet_mensal** | VARCHAR | Sim | CET mensal do contrato ativo |
| **cet_anual** | VARCHAR | Sim | CET anual do contrato ativo |
| **evidence** | JSONB | Sim | Evidência de extração |
| **created_at** | TIMESTAMP | Não | Data de criação |

#### Novas colunas em loan_contracts (Fase 2)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| **cet_mensal** | VARCHAR | CET mensal (ex: "1,81%") |
| **cet_anual** | VARCHAR | CET anual (ex: "24,14%") |
| **iof_cent** | BIGINT | IOF em centavos |
| **valor_emprestado_cent** | BIGINT | Valor efetivamente emprestado (diferente de valor_total) |

---

## 9. Cronograma e Dependências

### 9.1 Ordem de Implementação (Fase 1)

1. Migration + model INSSMargin (pré-requisito para tudo)
2. Extractor: parser de margem INSS + melhorar taxa_juros
3. Schema Pydantic: novos sub-schemas (LoanContractDetail, ConsignadoLineDetail, INSSMarginDetail)
4. API endpoint: expandir GET /jobs/{id}/result com queries relacionadas
5. Frontend types: novas interfaces TypeScript
6. Frontend componentes: 5 seções de PDF (cover, contracts, consignado, margin, methodology)
7. Frontend snapshot: redesign multi-página
8. Frontend export: lógica multi-página no jsPDF
9. Testes E2E: enviar PDFs de exemplo e validar relatório gerado

### 9.2 Estimativa de Esforço

| Fase | Escopo | Estimativa | Dependência |
|------|--------|------------|-------------|
| **Fase 1: Quick Wins** | Backend + Frontend | 2-3 sprints | Nenhuma |
| **Fase 2: Extração** | Backend (extractors) | 2-3 sprints | Fase 1 |
| **Fase 3: Avançado** | Full-stack | 1-2 sprints | Fase 2 |

### 9.3 Riscos e Mitigações

- **Risco:** html-to-image pode ter problemas com multi-página. **Mitigação:** renderizar cada página como div separada e converter individualmente.
- **Risco:** extrato INSS tem layouts variados entre beneficiários. **Mitigação:** manter regex + LLM fallback (já implementado no router).
- **Risco:** jobs antigos não terão dados novos. **Mitigação:** todos os campos novos são opcionais (null); PDF renderiza condicionalmente.
- **Risco:** performance de queries com joins adicionais. **Mitigação:** usar selectinload e índices em job_id (já existentes).

---

## 10. Critérios de Aceitação

### 10.1 Fase 1

- PDF gerado contém tabela de contratos com banco, parcela, prazo, saldo e taxa de juros para cada LoanContract ativo
- PDF contém linhas individuais do contracheque (quando não há LoanContract detalhado)
- PDF contém dados de margem INSS quando documento INSS foi processado
- PDF contém seção de ofertas (PRINCIPAL, REDUZIDA, SUPER)
- PDF tem 3-4 páginas com layout profissional
- Tempo de export < 10 segundos
- Relatórios de jobs antigos continuam funcionando (campos null = seção omitida)
- Nenhuma referência a fontes não consultadas (Serasa, Boa Vista, etc.)

### 10.2 Fase 2

- CET e IOF extraídos do extrato INSS com acurácia > 95%
- Custo real por contrato exibido: "Vai pagar R$ X para quitar R$ Y (R$ Z em juros)"
- Simulação de economia mostra parcela atual vs. parcela estimada com taxa de mercado
- Disclaimer em toda simulação: "Estimativa com taxa de referência — valores reais dependem de negociação"

### 10.3 Fase 3

- Seção "O que ainda não sabemos" com CTA para consultoria
- Timeline de refinanciamentos (quando histórico disponível)
- Mapa de dívidas com agrupamento por banco

---

## 11. Roadmap de Evolução de Dados

Conforme novas fontes forem integradas, a Camada 3 (dados não disponíveis) migra para a Camada 1 (confirmados):

| Versão | Fonte Adicionada | Impacto no Relatório |
|--------|-----------------|---------------------|
| **Atual** | Contracheque + Extrato Consignado | 8 métricas confirmadas + 3 indicações + CTA |
| **v2.1** | Integração com bureaus (Serasa API) | Score real, negativações, busca por crédito |
| **v2.2** | Registrato/SCR (autorização) | Mapa completo de dívidas no SFN |
| **v3.0** | Open Finance (consentimento) | Cheque especial, cartão, transações |

**Princípio:** cada fase melhora o relatório E reduz o que está na Camada 3, diminuindo o "o que não sabemos" e aumentando a proposta de valor do produto.

---

## 12. Questões em Aberto

| # | Questão | Quem decide | Impacto |
|---|---------|-------------|---------|
| 1 | A simulação deve usar taxa fixa interna ou taxas de parceiros? | Produto + Comercial | Fase 2 |
| 2 | O CTA do PDF direciona para WhatsApp, formulário ou telefone? | Comercial | Fase 1 |
| 3 | Deve haver branding/logo da empresa no PDF? | Design + Produto | Fase 1 |
| 4 | O relatório terá versão interativa (web) além do PDF? | Produto + Eng | Fase 3 |
| 5 | Qual disclaimer legal é obrigatório na simulação de economia? | Jurídico | Fase 2 |
| 6 | Migrar de html-to-image para @react-pdf/renderer? | Engenharia | Fase 1 |
| 7 | Exibir nomes completos dos credores ou apenas códigos de banco? | Jurídico + Produto | Fase 1 |

---

*Fim do documento. Versão 2.0 — 05/02/2026.*
