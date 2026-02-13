# Design - Capa PDF v2 (Antes e Depois)

## Contexto
A capa do relatório estava técnica, porém pouco orientada à tomada de decisão. O objetivo desta revisão foi tornar a página 1 mais intuitiva para o lead, destacando impacto financeiro mensal e anual sem depender de ofertas comerciais.

## Objetivo
Mostrar, em uma leitura rápida:
- situação atual (antes),
- cenário com redução (depois),
- economia mensal estimada e economia anual derivada.

## Decisões validadas
- Base da economia: `divida_mensal_cent - divida_mensal_reduzida_cent`.
- Linguagem principal: **Economia mensal estimada**.
- Sem uso de ofertas para compor o destaque da capa.
- Sem dependência de `savings_simulation` para o bloco principal da página 1.

## Estrutura da página 1
1. Cabeçalho
- Título: "Seu diagnóstico financeiro (antes e depois)".
- Data e identificação visual de relatório.

2. Painel principal
- Bloco **ANTES**: salário bruto, salário líquido, total de descontos, desconto mensal atual.
- Bloco **DEPOIS**: desconto mensal reduzido, novo salário líquido estimado e diferença mensal.
- Hierarquia visual: vermelho para pressão no orçamento, verde para alívio.

3. Destaque final da capa
- Card "Economia mensal estimada" com valor principal.
- Linha de reconciliação: `atual / mês -> reduzido / mês`.
- Complemento: economia anual estimada.

## Regras de cálculo
- `economia_mensal_cent = max(divida_mensal_cent - divida_mensal_reduzida_cent, 0)`
- `economia_anual_cent = economia_mensal_cent * 12`
- `salario_liquido_projetado_cent`:
  - preferencial: `max(salario_bruto_cent - divida_mensal_reduzida_cent, 0)`
  - fallback: `max(salario_liquido_cent + economia_mensal_cent, 0)`

Todos os cálculos permanecem em centavos; apenas a renderização usa formato BRL.

## Fallbacks
- Se não houver dados para estimar economia, exibir `R$ --` e mensagem: "Dados insuficientes para estimar a economia mensal.".
- Nenhum cálculo deve quebrar o render da página.
- Valores negativos são truncados para zero no cenário projetado.

## Arquivos impactados
- `frontend/src/components/pdf-sections/cover-summary.tsx`
- `frontend/src/components/result-snapshot.test.tsx`

## Critérios de aceite
- Capa comunica claramente antes/depois.
- Economia mensal e anual aparecem quando dados existem.
- Fallback aparece de forma explícita quando faltam dados.
- Render continua em uma única página sem overflow.
