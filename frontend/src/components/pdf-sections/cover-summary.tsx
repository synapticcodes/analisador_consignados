import { formatCurrency, type FinalResultResponse } from '@/types/api'
import { GrayBox, GreenHighlightBox, YellowCalloutBox } from './pdf-shared'
import { PDF_COLORS, type ConsolidatedSummary } from './pdf-utils'

type CoverSummaryProps = {
  result: FinalResultResponse
  clientName?: string
  clientCpf?: string
  isExtratoOnlyContext?: boolean
  consolidatedSummary?: ConsolidatedSummary | null
}

export function CoverSummary({
  result,
  clientName,
  clientCpf,
  isExtratoOnlyContext = false,
  consolidatedSummary,
}: CoverSummaryProps) {
  // ---- keep all original calculation logic unchanged ----
  const salarioBrutoCent = result.salario_bruto_cent
  const salarioLiquidoCent = result.salario_liquido_cent
  const totalDescontosCent = result.total_descontos_cent
  const dividaMensalCent = result.divida_mensal_cent
  const dividaMensalReduzidaCent = result.divida_mensal_reduzida_cent
  const baseCalculoCent = result.inss_margin?.base_calculo_cent ?? null
  const totalComprometidoCent = result.inss_margin?.total_comprometido_cent ?? null
  const consignadoMensalCent = result.consignado_mensal_cent

  const isBenefitContext =
    baseCalculoCent !== null &&
    totalComprometidoCent !== null &&
    (salarioBrutoCent === null || salarioBrutoCent === 0) &&
    (salarioLiquidoCent === null || salarioLiquidoCent === 0)

  const brutoLabel = isBenefitContext ? 'Benefício bruto' : 'Salário bruto'
  const liquidoLabel = isBenefitContext ? 'Benefício líquido' : 'Salário líquido'

  const brutoBaseCent = isBenefitContext ? baseCalculoCent : salarioBrutoCent
  const liquidoBaseCent =
    isBenefitContext && baseCalculoCent !== null && totalComprometidoCent !== null
      ? Math.max(baseCalculoCent - totalComprometidoCent, 0)
      : salarioLiquidoCent
  const totalDescontosBaseCent = isBenefitContext
    ? (totalComprometidoCent ?? totalDescontosCent)
    : totalDescontosCent
  const descontoMensalAtualCent = isBenefitContext ? totalComprometidoCent : dividaMensalCent
  const descontoMensalReduzidoCent =
    isBenefitContext && descontoMensalAtualCent !== null
      ? (dividaMensalReduzidaCent && dividaMensalReduzidaCent > 0
          ? dividaMensalReduzidaCent
          : Math.floor((descontoMensalAtualCent * 25) / 100))
      : dividaMensalReduzidaCent

  const consignadoCent = isBenefitContext
    ? descontoMensalAtualCent
    : (consignadoMensalCent ?? null)
  const outrosDescontosCent =
    totalDescontosBaseCent !== null && consignadoCent !== null
      ? Math.max(totalDescontosBaseCent - consignadoCent, 0)
      : null

  const economiaMensalCent =
    descontoMensalAtualCent !== null && descontoMensalReduzidoCent !== null
      ? Math.max(descontoMensalAtualCent - descontoMensalReduzidoCent, 0)
      : null

  const novoDescontoMensalCent =
    descontoMensalReduzidoCent !== null && outrosDescontosCent !== null
      ? descontoMensalReduzidoCent + outrosDescontosCent
      : descontoMensalReduzidoCent

  const salarioLiquidoProjetadoCent =
    brutoBaseCent !== null && novoDescontoMensalCent !== null && brutoBaseCent > 0
      ? Math.max(brutoBaseCent - novoDescontoMensalCent, 0)
      : brutoBaseCent !== null && descontoMensalReduzidoCent !== null && brutoBaseCent > 0
        ? Math.max(brutoBaseCent - descontoMensalReduzidoCent, 0)
        : liquidoBaseCent !== null && economiaMensalCent !== null
          ? Math.max(liquidoBaseCent + economiaMensalCent, 0)
          : null

  const displayEconomiaMensalCent = consolidatedSummary
    ? consolidatedSummary.economiaMensalParcelasCent
    : economiaMensalCent

  // ---- table rows ----
  type RowDef = {
    label: string
    atual: number | null
    projecao: number | null
    isRed?: boolean
    isGreen?: boolean
    isTotal?: boolean
  }

  const rows: RowDef[] = [
    { label: brutoLabel, atual: brutoBaseCent, projecao: brutoBaseCent },
    {
      label: 'Total descontado em folha',
      atual: totalDescontosBaseCent,
      projecao: novoDescontoMensalCent,
      isRed: true,
    },
    {
      label: 'Consignados',
      atual: consignadoCent,
      projecao: descontoMensalReduzidoCent,
    },
    {
      label: 'Outros descontos',
      atual: outrosDescontosCent,
      projecao: outrosDescontosCent,
    },
    {
      label: liquidoLabel,
      atual: liquidoBaseCent,
      projecao: salarioLiquidoProjetadoCent,
      isGreen: true,
      isTotal: true,
    },
  ]

  return (
    <section className="flex h-full flex-col" style={{ color: PDF_COLORS.textDark }}>
      {/* Title */}
      <div className="mb-1">
        <h1
          className="text-[22px] font-bold leading-tight"
          style={{ color: PDF_COLORS.darkBlue }}
        >
          Seu Diagnóstico Financeiro
        </h1>
        <p className="mt-1 text-[11px]" style={{ color: PDF_COLORS.mediumGray }}>
          {isExtratoOnlyContext
            ? 'Análise dos empréstimos consignados identificados no seu extrato INSS'
            : 'Análise dos empréstimos consignados identificados no seu contracheque'}
        </p>
      </div>

      {/* Client identification box */}
      {(clientName || clientCpf) && (
        <div
          className="mb-2 flex items-center justify-between rounded-sm px-4 py-3"
          style={{
            backgroundColor: PDF_COLORS.lightBlue,
            borderLeft: `4px solid ${PDF_COLORS.darkBlue}`,
          }}
        >
          <div className="space-y-0.5 text-[12px]" style={{ color: PDF_COLORS.textDark }}>
            {clientName && (
              <p>
                <span className="font-semibold">Cliente:</span>{' '}
                <span className="text-[14px] font-bold" style={{ color: PDF_COLORS.darkBlue }}>
                  {clientName.toUpperCase()}
                </span>
              </p>
            )}
            {clientCpf && (
              <p>
                <span className="font-semibold">CPF:</span>{' '}
                <span className="font-semibold" style={{ color: PDF_COLORS.darkBlue }}>
                  {clientCpf}
                </span>
              </p>
            )}
          </div>
        </div>
      )}

      {/* Yellow callout */}
      <YellowCalloutBox title="O que este documento mostra">
        <p>
          Este relatório apresenta uma comparação entre a situação atual dos seus empréstimos
          consignados e uma projeção de como ficariam após nossa atuação. Os valores projetados
          são estimativas baseadas em reduções já obtidas com perfis semelhantes.
        </p>
      </YellowCalloutBox>

      {/* Comparison table */}
      <div className="mt-3">
        <table className="w-full border-collapse text-[10px]">
          <thead>
            <tr style={{ backgroundColor: PDF_COLORS.darkBlue, color: PDF_COLORS.white }}>
              <th className="px-3 py-2 text-left font-semibold"> </th>
              <th className="px-3 py-2 text-right font-semibold">SITUAÇÃO ATUAL</th>
              <th className="px-3 py-2 text-right font-semibold">PROJEÇÃO RENEGOCIADA</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => {
              const bgColor = row.isTotal
                ? PDF_COLORS.lightGreen
                : i % 2 === 0
                  ? PDF_COLORS.white
                  : PDF_COLORS.warmGray
              const atualStyle = row.isRed
                ? { color: PDF_COLORS.accentRed, fontWeight: 700 as const }
                : {}
              const projecaoStyle = row.isGreen
                ? { color: PDF_COLORS.accentGreen, fontWeight: 700 as const }
                : row.isRed
                  ? { color: PDF_COLORS.accentGreen, fontWeight: 700 as const }
                  : {}
              return (
                <tr key={row.label} style={{ backgroundColor: bgColor }}>
                  <td
                    className="px-3 py-1.5 font-medium"
                    style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}` }}
                  >
                    {row.label}
                  </td>
                  <td
                    className="px-3 py-1.5 text-right"
                    style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}`, ...atualStyle }}
                  >
                    {formatCurrency(row.atual)}
                  </td>
                  <td
                    className="px-3 py-1.5 text-right"
                    style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}`, ...projecaoStyle }}
                  >
                    {formatCurrency(row.projecao)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div
        className="mt-2 rounded-sm px-3 py-2"
        style={{
          backgroundColor: PDF_COLORS.warmGray,
          border: `1px solid ${PDF_COLORS.borderGray}`,
        }}
      >
        <div className="grid grid-cols-4 gap-2">
          <div
            className="rounded-sm bg-white px-2 py-2 text-center"
            style={{ border: `1px solid ${PDF_COLORS.borderGray}` }}
          >
            <p className="text-[16px] font-bold" style={{ color: PDF_COLORS.darkBlue }}>
              +600 mil
            </p>
            <p className="text-[8px] leading-tight" style={{ color: PDF_COLORS.textSecondary }}>
              clientes atendidos
            </p>
          </div>
          <div
            className="rounded-sm bg-white px-2 py-2 text-center"
            style={{ border: `1px solid ${PDF_COLORS.borderGray}` }}
          >
            <p className="text-[16px] font-bold" style={{ color: PDF_COLORS.accentGreen }}>
              R$ 1 bi+
            </p>
            <p className="text-[8px] leading-tight" style={{ color: PDF_COLORS.textSecondary }}>
              em dívidas liquidadas
            </p>
          </div>
          <div
            className="rounded-sm bg-white px-2 py-2 text-center"
            style={{ border: `1px solid ${PDF_COLORS.borderGray}` }}
          >
            <p className="text-[16px] font-bold" style={{ color: PDF_COLORS.darkBlue }}>
              +7 anos
            </p>
            <p className="text-[8px] leading-tight" style={{ color: PDF_COLORS.textSecondary }}>
              de atuação
            </p>
          </div>
          <div
            className="rounded-sm bg-white px-2 py-2 text-center"
            style={{ border: `1px solid ${PDF_COLORS.borderGray}` }}
          >
            <p className="text-[16px] font-bold" style={{ color: PDF_COLORS.accentGreen }}>
              92%
            </p>
            <p className="text-[8px] leading-tight" style={{ color: PDF_COLORS.textSecondary }}>
              de ações com resultado favorável
            </p>
          </div>
        </div>
      </div>

      {/* Green economy highlight */}
      <div className="mt-3">
        <GreenHighlightBox>
          <p
            className="text-[10px] font-semibold uppercase tracking-wide"
            style={{ color: PDF_COLORS.accentGreen }}
          >
            Economia mensal estimada
          </p>
          <p
            className="mt-0.5 text-[28px] font-bold leading-tight"
            style={{ color: PDF_COLORS.accentGreen }}
          >
            {formatCurrency(displayEconomiaMensalCent)}
          </p>
          {displayEconomiaMensalCent === null && (
            <p className="mt-1 text-[10px]" style={{ color: PDF_COLORS.textSecondary }}>
              Dados insuficientes para estimar a economia mensal.
            </p>
          )}
        </GreenHighlightBox>
      </div>

      <div
        className="mt-3 rounded-sm px-4 py-3"
        style={{
          backgroundColor: PDF_COLORS.warmGray,
          borderLeft: `4px solid ${PDF_COLORS.accentGreen}`,
        }}
      >
        <p className="text-[10px] leading-relaxed" style={{ color: PDF_COLORS.textSecondary }}>
          {isExtratoOnlyContext
            ? '"Eu tinha 9 contratos de consignado e mal sobrava dinheiro pra viver. A Resolvver entrou com o processo e em 45 dias minhas parcelas caíram de R$ 2.800 pra R$ 720. Agora consigo pagar minhas contas sem sufoco."'
            : '"Vou ser sincero: achei que era golpe. Muita gente promete e não cumpre. Mas um colega de trabalho me indicou e eu resolvi tentar. Em menos de 2 meses minhas parcelas já tinham caído no contracheque. Me arrependo de não ter procurado antes."'}
        </p>
        <p className="mt-1 text-[10px] font-semibold" style={{ color: PDF_COLORS.textDark }}>
          {isExtratoOnlyContext
            ? '— M.S., servidor aposentado, São Paulo/SP'
            : '— C.L., servidor público federal, Brasília/DF'}
        </p>
      </div>

      {/* Gray explanation box */}
      <div className="mt-3">
        <GrayBox title="Como funciona a renegociação">
          <p className="mb-1">
            A renegociação consiste em revisar judicialmente os contratos de
            empréstimo consignado, buscando a redução das parcelas mensais
            descontadas em folha.
          </p>
          <p className="mb-1">
            Com base em decisões judiciais favoráveis, é possível reduzir
            o comprometimento mensal de cada contrato, mantendo os mesmos prazos e condições gerais.
          </p>
          <p>
            Os valores projetados neste relatório consideram uma estimativa de redução baseada
            no histórico de resultados obtidos pela Resolvver em ações judiciais de revisão de
            consignados. Na prática, as reduções concedidas pela Justiça variam conforme banco,
            tipo de contrato e condições específicas de cada caso.
          </p>
        </GrayBox>
      </div>

      {/* Footer note */}
      <p className="mt-auto pt-2 text-[8px]" style={{ color: PDF_COLORS.mediumGray }}>
        {isExtratoOnlyContext
          ? '* Os valores apresentados são baseados nos dados extraídos do extrato INSS fornecido. Condições reais podem variar conforme credor e perfil.'
          : '* Os valores apresentados são baseados nos dados extraídos do contracheque e/ou extrato de empréstimo consignado fornecidos. Condições reais podem variar conforme credor e perfil.'}
      </p>
    </section>
  )
}
