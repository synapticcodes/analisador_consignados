import { formatCurrency, type FinalResultResponse } from '@/types/api'
import { GrayBox, GreenHighlightBox, YellowCalloutBox } from './pdf-shared'
import { PDF_COLORS, type ConsolidatedSummary } from './pdf-utils'

type CoverSummaryProps = {
  result: FinalResultResponse
  clientName?: string
  dateLabel: string
  consolidatedSummary?: ConsolidatedSummary | null
}

export function CoverSummary({ result, clientName, dateLabel, consolidatedSummary }: CoverSummaryProps) {
  // ---- keep all original calculation logic unchanged ----
  const salarioBrutoCent = result.salario_bruto_cent
  const salarioLiquidoCent = result.salario_liquido_cent
  const totalDescontosCent = result.total_descontos_cent
  const dividaMensalCent = result.divida_mensal_cent
  const dividaMensalReduzidaCent = result.divida_mensal_reduzida_cent
  const baseCalculoCent = result.inss_margin?.base_calculo_cent ?? null
  const totalComprometidoCent = result.inss_margin?.total_comprometido_cent ?? null
  const dividaTotalConsignadaCent = result.divida_total_consignada_cent ?? null
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
    ? (dividaTotalConsignadaCent ?? totalDescontosCent)
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
          Seu Diagn&oacute;stico Financeiro
        </h1>
        <p className="mt-1 text-[11px]" style={{ color: PDF_COLORS.mediumGray }}>
          An&aacute;lise dos empr&eacute;stimos consignados identificados no seu contracheque
        </p>
      </div>

      {/* Client identification box */}
      {clientName && (
        <div
          className="mb-2 flex items-center justify-between rounded-sm px-4 py-3"
          style={{
            backgroundColor: PDF_COLORS.lightBlue,
            borderLeft: `4px solid ${PDF_COLORS.darkBlue}`,
          }}
        >
          <p className="text-[12px]" style={{ color: PDF_COLORS.textDark }}>
            <span className="font-semibold">Cliente:</span>{' '}
            <span className="text-[14px] font-bold" style={{ color: PDF_COLORS.darkBlue }}>
              {clientName.toUpperCase()}
            </span>
          </p>
        </div>
      )}

      {/* Yellow callout */}
      <YellowCalloutBox title="O que este documento mostra">
        <p>
          Este relat&oacute;rio apresenta uma compara&ccedil;&atilde;o entre a situa&ccedil;&atilde;o
          atual dos seus empr&eacute;stimos consignados e uma proje&ccedil;&atilde;o de como ficariam
          ap&oacute;s a renegocia&ccedil;&atilde;o. Os valores projetados s&atilde;o estimativas
          baseadas em redu&ccedil;&otilde;es j&aacute; obtidas com perfis semelhantes.
        </p>
      </YellowCalloutBox>

      {/* Comparison table */}
      <div className="mt-3">
        <table className="w-full border-collapse text-[10px]">
          <thead>
            <tr style={{ backgroundColor: PDF_COLORS.darkBlue, color: PDF_COLORS.white }}>
              <th className="px-3 py-2 text-left font-semibold">&nbsp;</th>
              <th className="px-3 py-2 text-right font-semibold">SITUA&Ccedil;&Atilde;O ATUAL</th>
              <th className="px-3 py-2 text-right font-semibold">PROJE&Ccedil;&Atilde;O RENEGOCIADA</th>
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

      {/* Gray explanation box */}
      <div className="mt-3">
        <GrayBox title="Como funciona a renegociação">
          <p className="mb-1">
            A renegocia&ccedil;&atilde;o consiste em revisar judicialmente os contratos de
            empr&eacute;stimo consignado, buscando a redu&ccedil;&atilde;o das parcelas mensais
            descontadas em folha.
          </p>
          <p className="mb-1">
            Com base em decis&otilde;es judiciais favor&aacute;veis, &eacute; poss&iacute;vel reduzir
            o comprometimento mensal de cada contrato, mantendo os mesmos prazos e condições gerais.
          </p>
          <p>
            Os valores projetados neste relat&oacute;rio consideram uma redu&ccedil;&atilde;o
            estimada de 75% no valor de cada parcela, refletindo o hist&oacute;rico de
            resultados obtidos pela Credilly em casos semelhantes.
          </p>
        </GrayBox>
      </div>

      {/* Footer note */}
      <p className="mt-auto pt-2 text-[8px]" style={{ color: PDF_COLORS.mediumGray }}>
        * Os valores apresentados s&atilde;o baseados nos dados extra&iacute;dos do contracheque
        e/ou extrato de empr&eacute;stimo consignado fornecidos. Condi&ccedil;&otilde;es reais
        podem variar conforme credor e perfil.
      </p>
    </section>
  )
}
