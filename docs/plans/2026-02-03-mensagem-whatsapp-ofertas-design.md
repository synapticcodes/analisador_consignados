# Design: Mensagem de WhatsApp com 3 ofertas

## Contexto
Após a conclusão da extração e cálculo, a página de resultados já apresenta as ofertas do produto. Foi solicitado um texto pronto para WhatsApp, com opção de copiar, usando as 3 ofertas exibidas.

## Objetivo
Exibir uma mensagem pronta (uma oferta por linha) na tela de resultados, abaixo das ofertas, com botão “Copiar”. A mensagem deve usar os valores formatados em BRL e não depender de mudanças no backend.

## Escopo
- Apenas frontend (`frontend/src/app/jobs/[id]/result/page.tsx`).
- Sem alterações na API ou backend.
- Gerar mensagem a partir de `result.offers`.

## UX e Comportamento
- O card “Mensagem para WhatsApp” aparece abaixo do bloco “Ofertas do Produto”.
- A mensagem é uma oferta por linha, sem rótulos e sem linha de abertura.
- Cada linha contém: texto da oferta + total + parcelas + entrada (se houver).
- Se houver menos de 3 ofertas, listar apenas as existentes.
- Se não houver ofertas, não renderizar o card.

## Formatação da Mensagem
- Estrutura base: `{offer.text} — Total: R$ X — Nx de R$ Y — Entrada: R$ Z em D dias`.
- Entrada é opcional; se `entry_value_cent` existir e `entry_due_days` for `null` ou `0`, usar “no ato”.
- Todos os valores devem usar `formatCurrency`.

## Implementação (alto nível)
- Função local `buildWhatsappMessage(offers)` para gerar o texto.
- Limitar a 3 ofertas por `offers.slice(0, 3)`.
- Renderizar o texto em `<textarea readOnly>` ou `<pre>` estilizado.
- Botão “Copiar” usa `navigator.clipboard.writeText(message)` com `toast` para sucesso/erro.

## Erros e Edge Cases
- Clipboard indisponível: mostrar `toast.error` e permitir cópia manual.
- `offers` vazio ou `null`: card não aparece.

## Testes (manual)
1. Resultado com 3 ofertas completas (com entrada).
2. Resultado com 1 oferta sem entrada.
3. Resultado com 0 ofertas (sem card).

## Trade-offs
- Frontend-only reduz risco e tempo, mas limita reuso da mensagem fora da UI.

## Riscos
- Ambientes sem suporte à Clipboard API exigem cópia manual.
