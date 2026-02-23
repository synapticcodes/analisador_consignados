# Mapeamento: Documentos Reais vs. 14 Indicadores

**Data:** 05/02/2026
**Documentos analisados:**
1. **Contracheque SIGEPE** — Roseli da Rosa Pereira (servidora federal UFRGS, Jan/2026)
2. **Histórico de Empréstimo Consignado INSS** — Maria do Carmo Oliveira de Sampaio (Pensão por Morte, 12 páginas)

---

## Dados Extraídos — Contracheque SIGEPE

| Dado | Valor |
|------|-------|
| Bruto | R$ 15.065,86 |
| Líquido | R$ 6.396,88 |
| Total de descontos | R$ 8.668,98 |
| INSS/PSS | R$ 1.494,21 |
| IRRF | R$ 2.413,81 |
| Sindical | R$ 119,66 |
| **Total em empréstimos consignados** | **R$ 4.612,85** (16 contratos) |
| Cartão de crédito consignado | R$ 28,45 (PAN) |
| **Total comprometido com crédito** | **R$ 4.641,30** |

**Detalhamento dos 16 empréstimos no contracheque:**

| Banco | Prazo | Parcela |
|-------|-------|---------|
| BRB CFI | 095 | R$ 769,55 |
| PRB | 085 | R$ 150,00 |
| PRB | 086 | R$ 417,00 |
| PRB | 086 | R$ 62,00 |
| PRB | 086 | R$ 64,53 |
| PRB | 095 | R$ 132,00 |
| PRB | 086 | R$ 288,33 |
| PAN | 051 | R$ 659,25 |
| PAN | 059 | R$ 175,00 |
| PAN | 059 | R$ 270,00 |
| PAN | 074 | R$ 120,00 |
| BCO SAF | 093 | R$ 265,39 |
| BCO SAF | 093 | R$ 418,27 |
| BCO SAF | 094 | R$ 117,00 |
| SANTANDER-OLE | 076 | R$ 223,53 |
| INBURSA | 090 | R$ 481,00 |
| **PAN (cartão)** | **001** | **R$ 28,45** |

---

## Dados Extraídos — Extrato INSS (12 páginas)

### Benefício
| Dado | Valor |
|------|-------|
| Tipo | Pensão por Morte Previdenciária |
| Nº Benefício | 076.111.137-9 |
| Situação | ATIVO |
| Banco | Sicoob, Ag. 6044 |
| Bloqueio para empréstimo | Bloqueado para empréstimo |
| Elegibilidade | Elegível para empréstimos |

### Margem (dados exatos do INSS)
| Dado | Valor |
|------|-------|
| Base de cálculo | R$ 1.621,00 |
| Máximo comprometimento permitido | R$ 729,45 |
| Total comprometido | R$ 611,35 |
| Margem extrapolada | R$ 0,00 |
| Margem disponível empréstimos | R$ 37,05 |
| Margem disponível RMC | R$ 0,00 |
| Margem disponível RCC | R$ 81,05 |

### Contrato Ativo (1 contrato)
| Dado | Valor |
|------|-------|
| Contrato | 153928 2128 |
| Banco | 121 - BANCO AGIBAN K SA |
| Origem | Averbação por Refinanciamento |
| Data inclusão | 13/10/2025 |
| Parcelas | 12 (11/2025 a 10/2026) |
| Valor da parcela | R$ 530,30 |
| Total emprestado | R$ 5.593,83 |
| IOF | R$ 7,45 |
| CET mensal | 1,81% |
| CET anual | 24,14% |
| Taxa juros mensal | 1,80% |
| Taxa juros anual | 23,87% |
| Valor pago (dívida do cliente) | R$ 5.265,13 |
| Primeiro desconto | 08/12/2025 |

### Contrato Suspenso (1 contrato)
- Não detalhado nas páginas visíveis

### Contratos Excluídos/Encerrados (20+ contratos, desde 2005)
Histórico completo de refinanciamentos e contratos com: AGIBAN, CETELEM (739), M-BNP (752), ITAÚ CONSIGNADO (029), PAN (623), BRADESCO FINANCIAMENTOS (394), BMG (318), CRUZEIRO DO SUL (229), PINE (643), ORIGINAL (212), BANRISUL (041)

**Padrão identificável:** Refinanciamentos consecutivos no mesmo banco (AGIBAN) — contratos excluídos por refinanciamento em 09/2025, 08/2025, 01/2025, mostrando ciclo de renovação frequente.

### Cartão de Crédito RMC
| Dado | Valor |
|------|-------|
| Contrato ativo | Banco Daycoval (707), desde 23/12/2015 |
| Limite | R$ 1.100,00 |
| Reservado (desconto mensal) | R$ 81,05 |
| Contrato encerrado | Banco BMG, Limite R$ 830,00 (excluído 10/2009) |
| Histórico de descontos | 60+ parcelas mensais de R$ 39,40 a R$ 52,25 (2016-2021) |

---

## Mapeamento: 14 Indicadores vs. Documentos

### Legenda
- ✅ **OBTIDO** — Dado disponível com precisão no documento
- ⚠️ **INFERÍVEL** — Pode ser calculado/inferido com ressalva
- ❌ **NÃO OBTIDO** — Não é possível extrair desses documentos

---

### #1 — Score de crédito
**❌ NÃO OBTIDO**

Nenhum dos documentos contém score de crédito. Essa métrica requer consulta direta aos bureaus (Serasa, Boa Vista, SPC, Quod). Não há como inferir o score numérico a partir de contracheque ou extrato INSS.

---

### #2 — Margem
**✅ OBTIDO (extrato INSS) / ⚠️ INFERÍVEL (contracheque)**

- **Extrato INSS:** Dados de margem com precisão absoluta — base de cálculo, máximo permitido, utilizado, disponível, por modalidade (empréstimo, RMC, RCC). Esta é a fonte oficial do INSS.
- **Contracheque:** Não mostra a margem explicitamente, mas pode ser calculada: para servidor federal, o limite é 35% do bruto para empréstimos + 5% para cartão. Com bruto de R$ 15.065,86, o máximo seria ~R$ 5.273 para empréstimos. O total em consignados é R$ 4.612,85, sobrando ~R$ 660. Porém esse cálculo depende de regras que variam por órgão.

**Conclusão: Margem é uma métrica REAL que esses documentos sustentam.**

---

### #3 — Cheque especial
**❌ NÃO OBTIDO**

Nenhum dos documentos contém informação sobre cheque especial. Requer Open Finance (dados bancários com consentimento).

---

### #4 — Juros invisíveis
**⚠️ PARCIALMENTE INFERÍVEL**

- **Extrato INSS:** Mostra taxa de juros do contrato ativo (1,80% a.m. / 23,87% a.a.) e CET (1,81% / 24,14%). Com isso, pode-se calcular: parcela R$ 530,30 × 12 = R$ 6.363,60 total pago, vs. R$ 5.265,13 de dívida real = **R$ 1.098,47 em juros neste contrato**.
- **Contracheque:** Mostra 16 empréstimos com parcelas, mas SEM taxas de juros. Sabemos que paga R$ 4.641,30/mês em empréstimos, mas não quanto disso é juros.

**Conclusão: Pode calcular juros do consignado INSS com precisão. Para os empréstimos do contracheque, só pode estimar com taxas médias de mercado (inferência com ressalva).**

---

### #5 — Chances de obter crédito
**❌ NÃO OBTIDO**

Requer dados de bureaus + Open Finance + Registrato. Nenhum documento fornece isso.

**Porém:** Pode-se inferir com forte ressalva — com 16 empréstimos simultâneos e margem quase zerada, as chances são objetivamente baixas. Mas isso é inferência, não dado.

---

### #6 — Risco de inadimplência
**❌ NÃO OBTIDO**

Requer dados de bureaus + Open Finance + Registrato.

**Porém:** A combinação de comprometimento alto + margem zero + múltiplos empréstimos permite uma inferência de risco elevado. Mas não é um dado, é uma conclusão.

---

### #7 — Comprometimento mensal
**✅ OBTIDO (ambos documentos)**

- **Contracheque:** R$ 4.641,30 (crédito) + R$ 1.494,21 (PSS) + R$ 2.413,81 (IRRF) + R$ 119,66 (sindical) = R$ 8.668,98 de descontos totais. Comprometimento: **57,5% do bruto** (ou 30,8% só em empréstimos).
- **Extrato INSS:** R$ 611,35 comprometido de R$ 1.621,00 de base = **37,7% em consignado**.

**Conclusão: Métrica totalmente calculável com precisão a partir dos documentos.**

---

### #8 — Uso do limite consolidado
**⚠️ PARCIALMENTE OBTIDO**

- **Extrato INSS:** Mostra uso da margem consignável — R$ 530,30 de R$ 567,35 = **93,5% utilizado** (empréstimos). RMC: 100% utilizado.
- **Contracheque:** Não mostra limites de cartão de crédito ou cheque especial, apenas parcelas de empréstimos.

**Conclusão: Pode calcular "uso da margem consignável" (que é um tipo de limite), mas não "uso do limite consolidado" que incluiria cartões e cheque especial.**

---

### #9 — Índice de busca por crédito
**❌ NÃO OBTIDO**

Requer consulta a bureaus (histórico de consultas). Nenhum documento contém isso.

**Porém:** O extrato INSS mostra 20+ contratos históricos com muitos bancos diferentes ao longo dos anos. Isso SUGERE busca intensa, mas não é o mesmo que o índice de consultas recentes.

---

### #10 — Perfil de bom-pagador
**⚠️ INFERÍVEL COM FORTE RESSALVA**

- **Extrato INSS:** Todos os contratos encerrados mostram situação "Encerrado" (não "Inadimplente"), e o contrato ativo está "Ativo" (não em atraso). Isso sugere que a pessoa paga em dia — mas o padrão de refinanciamentos consecutivos (3 refinanciamentos só no AGIBAN em 2025) indica dependência de rolagem.
- **Contracheque:** Descontos em folha são automáticos, então pagamentos estão em dia por definição (folha desconta antes de pagar).

**Conclusão: Pode inferir que "paga em dia porque é descontado em folha", mas o padrão de rolagem frequente indica fragilidade. Não substitui Cadastro Positivo dos bureaus.**

---

### #11 — Índice bola de neve
**⚠️ INFERÍVEL (extrato INSS — forte evidência)**

O extrato INSS é **surpreendentemente rico** para essa métrica:
- Contrato ativo: emprestado R$ 5.593,83, mas dívida do cliente (valor pago a título de refinanciamento) é R$ 5.265,13
- Histórico mostra: contrato excluído em 09/2025 (refinanciamento) → novo contrato excluído em 08/2025 (refinanciamento) → novo contrato excluído em 01/2025 (refinanciamento) → contrato ativo desde 10/2025
- **Padrão claro de rolagem:** a pessoa refinancia a mesma dívida repetidamente, provavelmente pegando valores cada vez maiores (averbação por refinanciamento)

**Conclusão: O histórico de refinanciamentos consecutivos é uma evidência forte de efeito bola de neve. Não é o cálculo exato (falta série temporal de saldos), mas é muito mais do que "genérico".**

---

### #12 — Confiança do diagnóstico
**N/A** — Métrica interna que depende de quais fontes foram consultadas.

Com apenas esses 2 documentos: confiança seria MÉDIA (2 de 5+ fontes possíveis).

---

### #13 — Projeção 12 meses
**⚠️ PARCIALMENTE INFERÍVEL**

- **Extrato INSS:** Contrato ativo termina em 10/2026 (12 parcelas). Se a pessoa mantiver, em 10/2026 estará livre do consignado INSS. Mas o padrão histórico mostra que ela provavelmente vai refinanciar antes.
- **Contracheque:** Com 16 contratos de prazos variados (051 a 095 meses), pode-se projetar quando cada um termina e quanto a parcela mensal cairá ao longo do tempo.

**Conclusão: Projeção do consignado é viável. Projeção "financeira completa" não é.**

---

### #14 — Resumo do relatório
**N/A** — Resumo depende dos indicadores anteriores.

---

## Resumo do Mapeamento

| # | Indicador | Contracheque | Extrato INSS | Veredicto |
|---|-----------|-------------|-------------|-----------|
| 1 | Score de crédito | ❌ | ❌ | **NÃO OBTIDO** |
| 2 | Margem | ⚠️ Calculável | ✅ Exato | **OBTIDO** |
| 3 | Cheque especial | ❌ | ❌ | **NÃO OBTIDO** |
| 4 | Juros invisíveis | ❌ Sem taxas | ⚠️ Taxas do ativo | **PARCIAL** |
| 5 | Chances de crédito | ❌ | ❌ | **NÃO OBTIDO** |
| 6 | Risco de inadimplência | ❌ | ❌ | **NÃO OBTIDO** |
| 7 | Comprometimento mensal | ✅ Exato | ✅ Exato | **OBTIDO** |
| 8 | Uso do limite consolidado | ❌ | ⚠️ Margem consig. | **PARCIAL** |
| 9 | Busca por crédito | ❌ | ❌ | **NÃO OBTIDO** |
| 10 | Perfil bom-pagador | ⚠️ Folha = em dia | ⚠️ Histórico rolagem | **INFERÍVEL** |
| 11 | Índice bola de neve | ❌ | ⚠️ Padrão refinanc. | **INFERÍVEL** |
| 12 | Confiança do diagnóstico | N/A | N/A | **META** |
| 13 | Projeção 12 meses | ⚠️ Prazos parciais | ⚠️ Prazo do ativo | **PARCIAL** |
| 14 | Resumo | N/A | N/A | **META** |

### Contagem final

| Status | Quantidade | Indicadores |
|--------|-----------|-------------|
| ✅ OBTIDO com precisão | **2** | Margem (#2), Comprometimento (#7) |
| ⚠️ PARCIAL ou INFERÍVEL | **5** | Juros (#4), Limite (#8), Bom-pagador (#10), Bola de neve (#11), Projeção (#13) |
| ❌ NÃO OBTIDO | **5** | Score (#1), Cheque especial (#3), Chances (#5), Inadimplência (#6), Busca (#9) |
| Meta/Resumo | **2** | Confiança (#12), Resumo (#14) |

---

## Descoberta Importante: O Extrato INSS É Muito Mais Rico do que Parece

O extrato INSS de 12 páginas contém dados que vocês talvez não estejam usando:

1. **Margem oficial exata** — não precisa calcular, o INSS já informa com centavos de precisão, separado por modalidade (empréstimo, RMC, RCC)

2. **Taxas de juros reais** — CET mensal/anual e taxa de juros do contrato ativo. Com isso, pode-se calcular o custo real da dívida

3. **Histórico de 20+ contratos desde 2005** — Mostra o histórico completo de empréstimos: quais bancos, quando refinanciou, quando excluiu, por qual motivo. Isso permite:
   - Contar quantos refinanciamentos recentes (padrão bola de neve)
   - Identificar se a dívida rola mais ou se reduz
   - Ver há quanto tempo a pessoa depende de consignado
   - Mapear quais bancos já foram usados

4. **Cartão de crédito RMC com histórico** — limite, reservado, e histórico de descontos mensais por anos

5. **Situação do benefício** — Ativo, elegível para empréstimo, tipo de benefício. Isso informa sobre as regras de margem que se aplicam.

### O que vocês provavelmente NÃO estão extraindo e deveriam:

| Dado no extrato INSS | Uso no relatório |
|----------------------|-----------------|
| Quantidade de refinanciamentos nos últimos 12 meses | Indicador bola de neve concreto: "3 refinanciamentos em 2025" |
| Número total de bancos diferentes no histórico | Evidência de busca por crédito: "12 bancos diferentes desde 2005" |
| Tempo desde o primeiro empréstimo consignado | Contexto: "Dependência de consignado há 20 anos" |
| Motivo de exclusão dos contratos | Padrão: "80% das exclusões por refinanciamento" = rolagem |
| Valor emprestado vs. valor pago (campo "Valor Pago**") | Custo real: "Pegou R$ 5.593 e vai pagar R$ 6.363 (R$ 770 de juros em 12 meses)" |
| Evolução dos valores de parcela ao longo dos anos | Tendência: parcelas subindo ou descendo? |

---

## Conclusão

Dos 14 indicadores originais, **apenas 2 são calculáveis com precisão** a partir desses documentos, **5 podem ser parcialmente inferidos**, e **5 são impossíveis** sem fontes externas.

Porém, os documentos — especialmente o extrato INSS — contêm dados valiosos que não estão nos 14 indicadores originais e que poderiam compor métricas novas e mais honestas:

- **Índice de rolagem** (quantos refinanciamentos em X meses) — dado real do extrato
- **Tempo de dependência do consignado** (anos desde primeiro contrato) — dado real
- **Custo real do contrato ativo** (emprestado vs. total a pagar) — calculável com precisão
- **Diversidade de credores** (quantos bancos no histórico) — dado real
- **Mapa parcial de dívidas** (lista de empréstimos em folha com banco e parcela) — dado real do contracheque
