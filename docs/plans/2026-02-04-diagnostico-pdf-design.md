# Diagnostico PDF/PNG - Design

## Objetivo
Gerar PDF (1 pagina A4) e imagem PNG com o diagnostico financeiro "antes e depois" a partir da tela de resultados, sem dependencia de backend.

## Escopo
- Geração no frontend com `html-to-image` e `jspdf`.
- Campos opcionais de nome do cliente e protocolo.
- Layout A4 retrato, com duas colunas (ANTES e DEPOIS) e destaque do alivio mensal.
- Sem logotipo ou branding adicional.
- Valores nulos exibidos como `--` e sem calculo do alivio.

## Layout
- Cabecalho: titulo fixo + linha com Cliente, Data e Protocolo (se informado).
- Coluna esquerda (ANTES): salario bruto, salario liquido, total de descontos e divida mensal estimada + alerta.
- Coluna direita (DEPOIS): divida mensal reduzida, divida total consignada e divida total reduzida.
- Destaque: economia mensal estimada com valor em destaque e frase explicativa.
- Rodape: "Como calculamos" + aviso curto de estimativa.

## Fluxo de geracao
1. Renderiza componente snapshot offscreen com dimensoes A4 (1240x1754).
2. Gera PNG com `html-to-image` e `pixelRatio: 2`.
3. Para PDF, embute o PNG em A4 via `jsPDF`.

## Tratamento de valores
- Formatos monetarios sempre usando `formatCurrency` (centavos).
- Se `divida_mensal_cent` ou `divida_mensal_reduzida_cent` for `null`, o bloco de alivio nao aparece.
- Quando faltarem dados de salario/descontos ou de divida total, exibir notas de orientacao no rodape.

## Arquivos
- `frontend/src/components/result-snapshot.tsx`: componente do layout.
- `frontend/src/app/jobs/[id]/result/page.tsx`: inputs e botoes de exportacao.
