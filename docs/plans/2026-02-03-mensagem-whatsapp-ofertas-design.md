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
- A mensagem tem uma linha de abertura fixa e duas linhas finais de fechamento.
- Cada oferta ocupa 2 linhas: rótulo + parcelas/1ª parcela.
- Ordem das ofertas: Reduzida, Principal, Super.
- Se houver menos de 3 ofertas, listar apenas as existentes.
- Se não houver ofertas, não renderizar o card.

## Formatação da Mensagem
Linha de abertura: `Separei N condições para você, todas no boleto e sem juros:`

Para cada oferta (duas linhas):
Rótulo: `⭐ Recomendada (melhor equilíbrio mensal)` / `Intermediária (menor valor total)` / `Curta (quita mais rápido)`
Detalhes: `Nx de R$ Y — 1ª parcela em D dias` (para SUPER com 1 dia, usar `1ª parcela amanhã`)

Fechamento:
`A maioria das pessoas com renda parecida com a sua opta pela recomendada, porque fica mais confortável no mês.`
`Qual faz mais sentido pra você?`

Usar `formatCurrency` para o valor da parcela e `first_payment_days` para a 1ª parcela.

## Implementação (alto nível)
- Função local `buildWhatsappMessage(offers)` para gerar o texto.
- Ordenar por tipo: `REDUZIDA`, `PRINCIPAL`, `SUPER` e limitar a 3.
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
