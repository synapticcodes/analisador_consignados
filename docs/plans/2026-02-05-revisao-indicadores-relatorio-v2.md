# PRD — Revisão dos Indicadores do Relatório Financeiro v2

**Data:** 05/02/2026
**Autor:** Claude (revisão técnica)
**Status:** Proposta para revisão
**Contexto:** Evolução da Calculadora de Consignados para diagnóstico financeiro completo via consulta CPF + Open Finance + bureaus

---

## 1. Resumo Executivo

O escopo atual contempla 14 indicadores financeiros gerados a partir de dados de bureaus de crédito (Serasa, Boa Vista, SPC, Quod), Banco Central (Open Finance, Registrato/SCR) e documentos enviados pelo usuário. O relatório é entregue como PDF para a pessoa física endividada, com objetivo de conversão em contratação de consultoria/assessoria.

**Veredito geral:** A base é sólida e cobre bem as dimensões de saúde financeira. Porém, existem 5 problemas estruturais que, se corrigidos, aumentam significativamente o poder de conversão e a clareza do relatório.

---

## 2. Os 5 Problemas Estruturais Identificados

### 2.1 Faltam valores numéricos — só há rótulos qualitativos

**Problema:** Todos os 14 indicadores mostram apenas rótulos como "CRÍTICO", "MUITO BAIXO", "DISPARANDO". Sem números, o relatório perde credibilidade e impacto emocional.

**Exemplo do problema:**
> Comprometimento mensal: INSUSTENTÁVEL

**Como deveria ser:**
> Comprometimento mensal: **87% da renda** (INSUSTENTÁVEL)

**Recomendação:** Cada indicador deve exibir o valor numérico calculado (percentual, valor em R$, ou score) acompanhado do rótulo de severidade. Isso dá concretude ao diagnóstico e torna impossível ignorar.

### 2.2 Escala de severidade inconsistente

**Problema:** Os rótulos de severidade variam sem padrão entre as métricas:

| Métrica | Rótulo usado |
|---------|-------------|
| Score de crédito | MUITO BAIXO |
| Margem | ZERADA |
| Cheque especial | CRÍTICO |
| Juros invisíveis | MUITO ALTO |
| Comprometimento | INSUSTENTÁVEL |
| Índice bola de neve | DISPARANDO |
| Perfil bom-pagador | MUITO FRÁGIL |
| Projeção 12 meses | PIORA ACELERADA |

**Recomendação:** Definir uma escala unificada de 5 níveis (alinhada com o resumo do relatório que já tem essa escala), e adicionar um **descritor contextual** por métrica:

- **Nível 1 — Estável** (verde)
- **Nível 2 — Atenção** (amarelo)
- **Nível 3 — Alto Risco** (laranja)
- **Nível 4 — Crítico** (vermelho)
- **Nível 5 — Alerta Máximo** (vermelho escuro)

Exemplo: `Comprometimento mensal: 87% da renda | Nível 5 — Alerta Máximo | "Quase toda a renda já está comprometida"`

Isso permite que o usuário entenda intuitivamente a gravidade relativa entre indicadores.

### 2.3 Sobreposições entre métricas

Três pares de indicadores têm sobreposição significativa que pode confundir o leitor:

**Par 1 — Score de crédito (#1) vs Chances de obter crédito (#5):**
O score é um *input* (dado bruto dos bureaus), as chances são uma *conclusão derivada* (leitura combinada). A distinção é válida, mas o relatório não deixa essa relação explícita. O usuário lê dois indicadores que parecem dizer a mesma coisa.
→ **Recomendação:** Tornar a #5 uma "leitura interpretada" que referencia explicitamente o score. Exemplo: "Com base no seu score (320/1000) e nos demais sinais, suas chances de crédito são..."

**Par 2 — Risco de inadimplência (#6) vs Projeção 12 meses (#13):**
Ambos projetam futuro. O #6 fala em "próximos meses" e o #13 em "3, 6 e 12 meses". Na prática, comunicam mensagens quase idênticas.
→ **Recomendação:** Fundir em um único indicador de projeção com 3 horizontes (3, 6, 12 meses), eliminando a métrica #6 como item separado. O risco de inadimplência vira um dos *outputs* da projeção.

**Par 3 — Juros invisíveis (#4) vs Índice bola de neve (#11):**
O #4 é a *causa* (quanto está pagando em juros ocultos) e o #11 é o *efeito* (se a dívida está reduzindo ou crescendo). A lógica é boa, mas o nome "juros invisíveis" e "bola de neve" não deixam clara essa relação causa-efeito.
→ **Recomendação:** Manter ambos, mas agrupar visualmente como "par" no relatório e adicionar uma frase de ligação: "Você paga R$ X/mês em juros que não percebe (#4), e esse custo faz sua dívida crescer mesmo pagando (#11)."

### 2.4 Ausência de métricas de conversão (o relatório "diagnostica" mas não "vende")

Como o objetivo é conversão em contratação de consultoria, o relatório termina no momento exato em que deveria começar a vender. Após 14 indicadores mostrando a gravidade, o leitor precisa de um *motivo imediato para agir*.

**Métricas ausentes que impactam diretamente conversão:**

**A) Mapa de Dívidas Ativas** — O relatório fala sobre risco e capacidade, mas em nenhum momento lista *quais* são as dívidas da pessoa. Isso é fundamental: o usuário precisa ver "eu tenho 4 dívidas totalizando R$ 47.000" para sentir a concretude do problema.

- Dados: Registrato/SCR (exposição no SFN), bureaus (negativações)
- Exibição: lista com credor, valor, taxa de juros (quando disponível), status

**B) Custo Total da Dívida (quanto vai pagar se não mudar)** — A métrica mais poderosa de conversão. "Se continuar pagando como está, você vai desembolsar R$ 73.000 para quitar R$ 47.000 de dívida." A diferença entre o que deve e o que vai acabar pagando é o argumento de venda.

- Dados: cálculo interno sobre taxas conhecidas via Open Finance + SCR
- Exibição: valor total projetado vs. saldo devedor atual

**C) Economia Potencial com Renegociação (simulação)** — "Se renegociar com as condições que costumamos conseguir, sua parcela cairia de R$ 2.300 para R$ 1.400/mês." Isso já existe parcialmente no design do diagnóstico "antes e depois" (2026-02-04), mas deveria fazer parte do relatório como indicador formal.

- Dados: simulação interna baseada em taxas de mercado praticáveis
- Exibição: antes/depois com economia mensal e total

### 2.5 Excesso de indicadores sem agrupamento

14 métricas em sequência linear é muita informação para um consumidor em situação de estresse financeiro. O leitor precisa de hierarquia visual para processar.

**Recomendação — Agrupar em 4 blocos:**

- **Bloco 1 — Retrato atual** (como você está): Score, Margem, Comprometimento mensal, Mapa de dívidas ativas
- **Bloco 2 — O que está drenando seu dinheiro** (por que não melhora): Juros invisíveis, Cheque especial, Uso do limite consolidado, Índice bola de neve
- **Bloco 3 — Como o mercado te enxerga** (acesso a crédito): Chances de obter crédito, Perfil de bom-pagador, Índice de busca por crédito
- **Bloco 4 — Para onde está indo** (projeção): Projeção unificada (3/6/12 meses), Custo total da dívida, Economia potencial

E o **Resumo** + **Confiança do diagnóstico** ficam como metadados (cabeçalho/rodapé).

---

## 3. Revisão Individual dos 14 Indicadores

### #1 — Score de crédito ✅ Manter (com ajustes)
**O que está bom:** Métrica consagrada, fonte confiável, o usuário já ouviu falar.
**Ajuste:** Mostrar o valor numérico do score (ex: 320/1000) e não apenas "MUITO BAIXO". Indicar também a faixa de referência (0-300 = Muito Baixo, 301-500 = Baixo, etc.). Considerar mostrar o score de cada bureau separadamente para transparência.

### #2 — Margem ✅ Manter
**O que está bom:** Métrica prática e de fácil compreensão. Diretamente acionável.
**Ajuste:** Exibir o valor em R$ (ex: "Margem disponível: R$ 0,00 — ZERADA"). Se possível, mostrar o breakdown: renda bruta → descontos obrigatórios → consignados existentes → margem.

### #3 — Cheque especial ✅ Manter (com ajuste de nome)
**O que está bom:** Identifica um dos maiores drenos financeiros do brasileiro.
**Ajuste:** Renomear para "Dependência do cheque especial" para ser mais descritivo. Mostrar: frequência de uso no período analisado, valor médio utilizado, custo estimado em juros.

### #4 — Juros invisíveis ✅ Manter (com valor)
**O que está bom:** Conceito original e impactante. Fala a língua do consumidor.
**Ajuste:** PRECISA mostrar o valor em R$. "Você está pagando aproximadamente R$ 890/mês em juros que não percebe" é infinitamente mais impactante que "MUITO ALTO".

### #5 — Chances de obter crédito ✅ Manter (conectar ao score)
**O que está bom:** Traduz o score em linguagem prática.
**Ajuste:** Referenciar explicitamente o score (#1) como um dos inputs. Usar percentual estimado quando possível: "Aproximadamente 15% de chance de aprovação com condições razoáveis."

### #6 — Risco de inadimplência ⚠️ Fundir com Projeção (#13)
**Motivo:** Sobreposição com a projeção de 12 meses. Ambos respondem "o que vai acontecer se nada mudar".
**Proposta:** Eliminar como indicador separado. Incorporar como um dos outputs da Projeção unificada: "Em 3 meses: risco de atraso em 2+ contas. Em 6 meses: possível negativação. Em 12 meses: situação agrava significativamente."

### #7 — Comprometimento mensal ✅ Manter (com valor)
**O que está bom:** Métrica fundamental. Todo mundo entende "quanto sobra do meu salário".
**Ajuste:** Mostrar como percentual E valor: "R$ 3.200 de R$ 3.680 já comprometidos (87%)". Incluir o que fica: "Sobra R$ 480 para alimentação, transporte e imprevistos."

### #8 — Uso do limite consolidado ✅ Manter
**O que está bom:** Indicador importante de dependência de crédito.
**Ajuste:** Mostrar valores: "R$ 14.200 de R$ 15.000 de limite utilizado (94,7%)". Separar por tipo: cartão de crédito vs. cheque especial vs. outros.

### #9 — Índice de busca por crédito ✅ Manter
**O que está bom:** Métrica que poucos consumidores conhecem. Efeito educativo alto.
**Ajuste:** Mostrar o número de consultas: "12 consultas nos últimos 6 meses (CRÍTICO — a média saudável é até 3)." Isso educa o consumidor sobre um comportamento que ele pode mudar imediatamente.

### #10 — Perfil de bom-pagador ✅ Manter
**O que está bom:** Contraponto positivo. Mostra que existe um caminho de recuperação.
**Ajuste:** Ser mais específico: "Nos últimos 12 meses: 4 de 12 pagamentos em dia, 6 com mínimo do cartão, 2 atrasos superiores a 30 dias."

### #11 — Índice bola de neve ✅ Manter (destaque especial)
**O que está bom:** Indicador original e muito comunicativo. Provavelmente o mais impactante do relatório.
**Ajuste:** Este merece destaque visual no relatório. Mostrar com mini-gráfico se possível: "Nos últimos 6 meses, você pagou R$ 8.400 em parcelas, mas sua dívida subiu R$ 2.100." Isso é devastadoramente claro.

### #12 — Confiança do diagnóstico ✅ Manter (como metadado)
**O que está bom:** Transparência sobre a completude da análise. Diferenciador competitivo.
**Ajuste:** Mover para cabeçalho ou rodapé do relatório (não compete como indicador). Mostrar checklist das fontes: "✓ Serasa ✓ Boa Vista ✓ Open Finance ✗ Registrato (não autorizado) — Confiança: 78%."

### #13 — Projeção 12 meses ✅ Manter (absorvendo #6)
**O que está bom:** Cria urgência. Essencial para conversão.
**Ajuste:** Absorver o risco de inadimplência (#6). Mostrar cenário em 3 marcos temporais concretos: "Em 3 meses: [situação]. Em 6 meses: [situação]. Em 12 meses: [situação]." Se possível, incluir dois cenários: "se nada mudar" vs. "se agir agora".

### #14 — Resumo do relatório ✅ Manter (com CTA)
**O que está bom:** A escala de 5 níveis é clara. O texto gera urgência.
**Ajuste:** Adicionar call-to-action explícito. O resumo deve terminar com uma ação concreta: "Fale com um consultor agora" / "Agende sua análise personalizada" / botão/QR code.

---

## 4. Novas Funcionalidades Propostas

### Nova #1 — Mapa de Dívidas Ativas (Prioridade: ALTA)

**Justificativa:** O consumidor precisa ver suas dívidas listadas para sentir a concretude do problema. Sem isso, o relatório fala "em tese" — com isso, fala sobre *a vida dele*.

**Estrutura proposta:**

- Lista de dívidas encontradas: credor, tipo (cartão, empréstimo, financiamento), valor original, saldo devedor atual, taxa de juros, status (em dia, atraso, negativado)
- Totalizador: número de contratos, valor total devido, custo mensal total
- Fonte: Registrato/SCR, bureaus (negativações), Open Finance (contratos ativos)

**Posição no relatório:** Bloco 1 — Retrato atual

### Nova #2 — Custo Total da Dívida (Prioridade: ALTA)

**Justificativa:** A métrica de conversão mais poderosa. "Você deve R$ 47.000, mas vai acabar pagando R$ 73.000 se continuar assim." A diferença de R$ 26.000 é dinheiro jogado fora — e é o argumento que vende consultoria.

**Estrutura proposta:**

- Saldo devedor total atual
- Projeção de quanto vai pagar até quitar (com taxas atuais)
- Diferença: "custo extra" dos juros
- Comparação simplificada: "Isso equivale a X meses do seu salário"

**Posição no relatório:** Bloco 4 — Para onde está indo

### Nova #3 — Economia Potencial / Simulação de Reorganização (Prioridade: MUITO ALTA)

**Justificativa:** O design do diagnóstico "antes e depois" (plano de 04/02) já contempla economia mensal estimada. Mas isso precisa ser um indicador formal no relatório, não apenas um anexo visual. É o "gancho" final de conversão.

**Estrutura proposta:**

- Cenário atual: parcela mensal total, prazo remanescente, custo total projetado
- Cenário reorganizado: parcela mensal estimada, novo prazo, novo custo total
- Diferença: economia mensal, economia total, "meses de respiro" ganhos
- Disclaimer: "Simulação baseada em condições de mercado. Valores finais dependem de negociação."

**Posição no relatório:** Último bloco antes do resumo (é o clímax do relatório)

### Nova #4 — Comparativo com Perfil Similar (Prioridade: MÉDIA)

**Justificativa:** "Você compromete 87% da renda. Pessoas na sua faixa de renda comprometem em média 45%." Esse tipo de benchmark social é extremamente eficaz para gerar senso de urgência sem parecer alarmista — é um fato comparativo.

**Estrutura proposta:**

- Para 2-3 indicadores-chave (comprometimento, uso de limite, score), mostrar a média de pessoas com perfil de renda similar
- Não precisa ser exato. Pode usar faixas baseadas em dados públicos do Banco Central (relatórios de estabilidade financeira, pesquisas de endividamento do IBGE/Fecomércio)

**Posição no relatório:** Inline nos indicadores relevantes (como sub-texto)

### Nova #5 — Alertas de Ação Imediata (Prioridade: MÉDIA)

**Justificativa:** Alguns indicadores pedem ação imediata que o consumidor pode tomar *hoje*, sem consultoria. Exemplo: "Pare de buscar crédito — cada consulta piora seu score." Isso gera credibilidade ("eles me ajudaram de graça") e confiança, aumentando a chance de conversão para o serviço pago.

**Estrutura proposta:**

- 2 a 3 micro-ações baseadas nos indicadores mais críticos
- Formato: "Faça isso hoje" + explicação de 1 linha
- Exemplos: "Pare de buscar crédito por 30 dias", "Negocie o cheque especial para crédito pessoal (taxa menor)", "Solicite portabilidade do consignado"

**Posição no relatório:** Dentro do resumo ou como seção "Primeiros Passos"

---

## 5. Estrutura Revisada do Relatório (Proposta)

**Mapeamento:** Dos 14 indicadores originais, o #6 (Risco de Inadimplência) é absorvido pelo #13 (Projeção). Os indicadores #12 (Confiança) e #14 (Resumo) saem da sequência principal e viram elementos estruturais (cabeçalho e rodapé). Isso resulta em **11 indicadores originais ativos + 4 novos = 15 indicadores no corpo do relatório**, mais 2 elementos estruturais e dados contextuais inline.

### Cabeçalho (elemento estrutural, ex-#12)
- Dados do cliente (nome, CPF parcial, data)
- Confiança do diagnóstico (ex: 78% — checklist de fontes)

### Bloco 1 — Retrato Atual (4 indicadores)
1. Score de crédito (valor numérico + classificação) — *ex-#1*
2. Margem consignável (valor em R$ + status) — *ex-#2*
3. Comprometimento mensal (percentual + valor absoluto) — *ex-#7*
4. **[NOVO]** Mapa de dívidas ativas (lista + totalizador)

### Bloco 2 — O Que Está Drenando Seu Dinheiro (4 indicadores)
5. Juros invisíveis (valor em R$/mês) — *ex-#4*
6. Dependência do cheque especial (frequência + custo) — *ex-#3, renomeado*
7. Uso do limite consolidado (percentual + valores) — *ex-#8*
8. Índice bola de neve (destaque — quanto pagou vs. quanto a dívida variou) — *ex-#11*

### Bloco 3 — Como o Mercado Te Enxerga (3 indicadores)
9. Chances de obter crédito (percentual estimado) — *ex-#5*
10. Perfil de bom-pagador (detalhamento de pontualidade) — *ex-#10*
11. Índice de busca por crédito (número de consultas + referência) — *ex-#9*

*Dados contextuais inline:* Comparativo com perfil similar (benchmarks em 2-3 indicadores-chave)

### Bloco 4 — Para Onde Está Indo (2 indicadores)
12. Projeção unificada 3/6/12 meses (absorve ex-#6 + ex-#13)
13. **[NOVO]** Custo total da dívida (quanto vai pagar vs. quanto deve)

### Bloco 5 — O Que Pode Mudar (2 indicadores)
14. **[NOVO]** Simulação de reorganização (antes/depois + economia)
15. **[NOVO]** Alertas de ação imediata (2-3 micro-ações)

### Resumo e CTA (elemento estrutural, ex-#14)
- Badge de nível (1-5) com texto de urgência
- **[NOVO]** Call-to-action explícito (falar com consultor, agendar análise)

### Rodapé
- Metodologia resumida
- Disclaimer legal

---

## 6. Resumo das Recomendações

| # | Recomendação | Impacto | Esforço |
|---|-------------|---------|---------|
| 1 | Adicionar valores numéricos a todos os indicadores | ALTO (credibilidade) | BAIXO |
| 2 | Unificar escala de severidade em 5 níveis | MÉDIO (clareza) | BAIXO |
| 3 | Fundir Risco de Inadimplência (#6) com Projeção (#13) | MÉDIO (reduz ruído) | BAIXO |
| 4 | Agrupar indicadores em 4-5 blocos temáticos | ALTO (legibilidade) | MÉDIO |
| 5 | Adicionar Mapa de Dívidas Ativas | ALTO (concretude) | MÉDIO |
| 6 | Adicionar Custo Total da Dívida | MUITO ALTO (conversão) | MÉDIO |
| 7 | Adicionar Simulação de Reorganização / Economia Potencial | MUITO ALTO (conversão) | ALTO |
| 8 | Adicionar call-to-action no resumo | ALTO (conversão) | BAIXO |
| 9 | Adicionar Comparativo com Perfil Similar | MÉDIO (urgência social) | MÉDIO |
| 10 | Adicionar Alertas de Ação Imediata | MÉDIO (confiança) | BAIXO |
| 11 | Conectar Score (#1) com Chances (#5) explicitamente | BAIXO (clareza) | BAIXO |
| 12 | Agrupar Juros Invisíveis (#4) com Bola de Neve (#11) como par causa-efeito | MÉDIO (compreensão) | BAIXO |
| 13 | Mover Confiança do Diagnóstico para cabeçalho/rodapé | BAIXO (organização) | BAIXO |

---

## 7. Priorização Sugerida para Implementação

**Fase 1 — Quick wins (1-2 sprints):**
- Valores numéricos em todos os indicadores
- Escala de severidade unificada
- Fusão #6 + #13
- Agrupamento em blocos
- CTA no resumo
- Confiança como metadado

**Fase 2 — Métricas de conversão (2-3 sprints):**
- Mapa de dívidas ativas
- Custo total da dívida
- Simulação de reorganização (integrar com design "antes/depois" existente)

**Fase 3 — Refinamento (1-2 sprints):**
- Comparativo com perfil similar
- Alertas de ação imediata
- Conexões explícitas entre métricas relacionadas
- Mini-gráficos para bola de neve e projeção

---

## 8. Considerações Técnicas

**Fontes de dados para novas métricas:**
- Mapa de dívidas: Registrato/SCR (já contemplado) + bureaus (já integrados) → requer apenas consolidação
- Custo total: cálculo interno sobre dados já capturados (taxas do Open Finance + saldos do SCR)
- Simulação: requer definição de taxas-alvo de mercado para renegociação (parâmetro configurável)
- Comparativo: dados estáticos de pesquisas públicas (IBGE, Fecomércio, BC) — atualização trimestral

**Impacto no PDF:**
- Relatório passa de ~2 páginas para ~3-4 páginas com as adições
- Blocos temáticos permitem layout mais visual (boxed sections)
- Mini-gráficos (bola de neve, projeção) requerem geração de SVG ou canvas no frontend

**LGPD:**
- Mapa de dívidas ativas contém dados sensíveis. Garantir que o PDF tenha identificação parcial dos credores ou exija confirmação de identidade para visualização
- Comparativo com perfil similar deve usar dados agregados/anônimos (sem referência a indivíduos)

---

## 9. REVISÃO CRÍTICA — Estratégia de Dados (atualização 05/02)

### Contexto revelado

Os dados reais disponíveis hoje são **exclusivamente contracheque e consignado** (documentos enviados pelo lead). As fontes listadas no escopo original (Serasa, Boa Vista, SPC, Quod, Open Finance, Registrato/SCR) **não são consultadas**. Todos os leads chegam via WhatsApp/formulário e possuem métricas ruins (viés de seleção — quem procura ajuda já está em dificuldade).

### Problema #1: Fontes fictícias destroem credibilidade

Listar "Dados obtidos de: Serasa Experian, Boa Vista, SPC Brasil, Quod" quando esses dados nunca foram consultados é arriscado. Se o lead verificar (e muitos conhecem o Registrato, o consumidor.gov.br), a confiança no relatório e na empresa cai a zero. Além disso, há risco regulatório: apresentar um diagnóstico como fundamentado em fontes não consultadas pode configurar propaganda enganosa.

**Ação imediata:** Remover todas as referências a fontes não consultadas. Substituir por "Dados obtidos de: Documentos enviados (contracheque e extrato de consignado)" — que é verdade.

### Problema #2: 14 métricas com dados de 2 fontes é insustentável

Com apenas contracheque + consignado, não é possível calcular com honestidade métricas como: score de crédito, cheque especial, juros invisíveis, chances de crédito, índice de busca por crédito, perfil de bom-pagador, ou índice bola de neve. Essas métricas dependem de dados que vocês não possuem.

Tentar preencher essas métricas com inferências genéricas (que são iguais para todos os leads) torna o relatório um template disfarçado de diagnóstico personalizado.

### Problema #3: "Todos são CRÍTICO" = nenhum é CRÍTICO

Se 100% dos leads recebem "CRÍTICO" em quase tudo, o diagnóstico não diferencia ninguém e vira ruído. O lead sabe que está mal — ele veio pedir ajuda. O que ele precisa é de **especificidade**: *quanto* está mal, *onde* exatamente, e *o que muda* se agir.

---

### Estratégia proposta: 3 camadas de dados

#### Camada 1 — CONFIRMADO (dados reais do contracheque + consignado)

Estas métricas podem ser calculadas com precisão a partir dos documentos enviados:

| # | Métrica | Dado real disponível | Exemplo de valor |
|---|---------|---------------------|-----------------|
| 1 | **Salário bruto** | Contracheque | R$ 3.680,00 |
| 2 | **Salário líquido** | Contracheque | R$ 2.944,00 |
| 3 | **Margem consignável** | Contracheque (35% bruto - consignados existentes) | R$ 0,00 (zerada) |
| 4 | **Comprometimento com consignado** | Parcela ÷ líquido | 41% do líquido (R$ 1.208/mês) |
| 5 | **Taxa de juros do consignado** | Extrato do empréstimo | 2,14% a.m. (CET 28,9% a.a.) |
| 6 | **Prazo restante** | Extrato do empréstimo | 48 parcelas (4 anos) |
| 7 | **Custo total projetado** | Parcela × prazo restante vs. saldo devedor | Vai pagar R$ 58.000 para quitar R$ 39.000 (R$ 19.000 só em juros) |
| 8 | **Economia potencial via portabilidade** | Simulação com taxa de mercado mais baixa | Parcela pode cair de R$ 1.208 para R$ 980/mês (economia de R$ 10.944 no total) |

**Estas 8 métricas são verificáveis, personalizadas (variam de lead para lead) e diretamente acionáveis.** São o núcleo do relatório.

#### Camada 2 — INDICAÇÃO (inferências legítimas, com ressalva explícita)

Com base nos dados da Camada 1, algumas conclusões são razoáveis — desde que apresentadas como indicações, não como fatos:

| # | Indicação | Lógica | Ressalva |
|---|-----------|--------|----------|
| 9 | **Risco financeiro** | Se comprometimento > 70% e margem = 0, o risco é alto | "Baseado nos dados disponíveis — uma análise completa pode revelar outros fatores" |
| 10 | **Tendência se nada mudar** | Projeção simples: parcelas restantes × taxa vs. amortização | "Estimativa simplificada — não considera mudanças de renda ou novas dívidas" |
| 11 | **Posição relativa** | Comparação com médias públicas (ex: endividamento médio do brasileiro segundo BC/IBGE) | "Comparação com dados agregados públicos — seu perfil individual pode diferir" |

**Apresentar sempre com: "Com base nos documentos analisados, indica-se que..."** — nunca como "CONFIRMADO".

#### Camada 3 — NÃO DISPONÍVEL (usar como gancho de conversão)

Estas métricas requerem fontes que vocês não têm. Em vez de inventar, transformem em argumento de venda:

| Métrica que NÃO pode ser calculada | Por quê | Gancho de conversão |
|-------------------------------------|---------|-------------------|
| Score de crédito real | Requer consulta aos bureaus | "Na consultoria, fazemos a consulta real do seu score" |
| Negativações e protestos | Requer Serasa/SPC/Boa Vista | "Descubra exatamente onde está negativado e como limpar" |
| Todas as dívidas (mapa completo) | Requer Registrato/SCR | "Veja todas as suas dívidas em todos os bancos" |
| Uso de cheque especial e cartão | Requer Open Finance | "Entenda quanto está perdendo com juros de cartão e cheque especial" |
| Índice de busca por crédito | Requer bureaus | "Saiba se as consultas estão prejudicando sua aprovação" |

**Formato sugerido no relatório:** Uma seção chamada "O que ainda não sabemos sobre você" com 3-4 itens e CTA: "Com a consultoria completa, revelamos o quadro inteiro."

---

### Estrutura revisada do relatório (com dados reais)

**Página 1 — Seu Retrato Financeiro (Camada 1: dados confirmados)**
- Bloco salário: bruto, líquido, descontos
- Bloco consignado: parcela, taxa, prazo, saldo
- Destaque: Comprometimento mensal (% com gráfico simples) + Margem disponível
- Destaque: Custo total da dívida ("você vai pagar X para quitar Y")

**Página 2 — O Que Pode Mudar (Camada 1 + Camada 2)**
- Simulação de economia: cenário atual vs. cenário renegociado
- Indicações de risco e tendência (com ressalvas)
- Comparativo com médias nacionais (dados públicos)

**Página 3 — O Quadro Completo (Camada 3: gancho de conversão)**
- "O que ainda não sabemos" — lista de métricas que requerem análise completa
- CTA: agendar consultoria para diagnóstico completo
- Depoimento/caso de exemplo (se tiver): "Fulano economizou R$ 15.000 após renegociação"

---

### Impacto na conversão

Esta abordagem é **mais eficaz comercialmente** do que 14 métricas genéricas porque:

1. **Credibilidade:** Tudo que está no relatório é verdade e verificável. O lead pode conferir no contracheque.
2. **Especificidade:** "R$ 19.000 só em juros" impacta muito mais que "JUROS INVISÍVEIS: MUITO ALTO."
3. **Curiosidade:** A Camada 3 cria desejo de saber mais ("o que mais eu não estou vendo?").
4. **Ação clara:** A economia potencial dá um motivo concreto e mensurável para contratar a consultoria.
5. **Diferenciação:** Em vez de parecer mais uma ferramenta genérica de "diagnóstico financeiro", vocês entregam números reais. Isso é raro no mercado.

### Roadmap de evolução de dados

| Fase | O que adicionar | Impacto no relatório |
|------|----------------|---------------------|
| **Atual** | Contracheque + consignado | 8 métricas confirmadas + 3 indicações + CTA |
| **v2.1** | Integração com bureaus (Serasa API) | Adiciona score real, negativações, busca por crédito → Camada 3 vira Camada 1 |
| **v2.2** | Registrato/SCR (com autorização) | Mapa completo de dívidas no SFN → relatório vira diagnóstico 360° |
| **v3.0** | Open Finance (consentimento bancário) | Cheque especial, cartão, transações → todas as 14+ métricas originais viáveis |

**Cada fase melhora o relatório E reduz o que está na Camada 3, diminuindo o "o que não sabemos" e aumentando a proposta de valor do produto em si (menos dependência da consultoria para dados básicos).**

---

## 10. Questões em Aberto

| # | Questão | Quem decide |
|---|---------|-------------|
| 1 | A simulação de reorganização deve usar taxas fixas internas ou taxas variáveis de parceiros? | Produto + Comercial |
| 2 | O mapa de dívidas deve mostrar nomes de credores ou apenas categorias (banco, financeira, varejo)? | Jurídico + Produto |
| 3 | Os dados do comparativo virão de pesquisas públicas ou de base própria anonimizada? | Data + Jurídico |
| 4 | O CTA do relatório direciona para WhatsApp, formulário web, ou telefone? | Comercial |
| 5 | O relatório terá versão interativa (web) além do PDF? | Produto + Eng |
| 6 | Qual é o threshold mínimo de fontes para gerar o relatório (ex: mínimo 3 de 5 fontes)? | Produto |
