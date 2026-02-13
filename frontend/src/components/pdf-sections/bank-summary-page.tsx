import { formatCurrency } from '@/types/api'
import { HorizontalCommitmentBar } from './pdf-shared'
import { PDF_COLORS, formatPercent, type BankGroup, type ConsolidatedSummary } from './pdf-utils'

type BankSummaryPageProps = {
  bankGroups: BankGroup[]
  consolidatedSummary: ConsolidatedSummary
}

export function BankSummaryPage({ bankGroups, consolidatedSummary }: BankSummaryPageProps) {
  const totalParcelaAtualCent = bankGroups.reduce((s, g) => s + g.parcelaAtualCent, 0)
  const totalNovaParcelaCent = bankGroups.reduce((s, g) => s + g.novaParcelaCent, 0)
  const totalEconomiaCent = bankGroups.reduce((s, g) => s + g.economiaCent, 0)
  const totalContratos = bankGroups.reduce((s, g) => s + g.contratos, 0)
  const hasProjectedTotals =
    consolidatedSummary.totalAtualFinalCent > 0 ||
    consolidatedSummary.totalComReducaoFinalCent > 0 ||
    consolidatedSummary.economiaTotalFinalCent > 0

  return (
    <section className="flex h-full flex-col" style={{ color: PDF_COLORS.textDark }}>
      <h2 className="text-[16px] font-bold" style={{ color: PDF_COLORS.darkBlue }}>
        Resumo por Banco
      </h2>
      <p className="mt-0.5 text-[10px]" style={{ color: PDF_COLORS.mediumGray }}>
        Visão consolidada dos empréstimos agrupados por instituição financeira.
      </p>

      {/* Bank table */}
      <div className="mt-3">
        <table className="w-full border-collapse text-[10px]">
          <thead>
            <tr style={{ backgroundColor: PDF_COLORS.darkBlue, color: PDF_COLORS.white }}>
              <th className="px-2 py-1.5 text-left font-semibold">Banco</th>
              <th className="px-2 py-1.5 text-center font-semibold">Contratos</th>
              <th className="px-2 py-1.5 text-right font-semibold">Parcela atual</th>
              <th className="px-2 py-1.5 text-right font-semibold">Nova parcela</th>
              <th className="px-2 py-1.5 text-right font-semibold">Economia/mês</th>
              <th className="px-2 py-1.5 text-right font-semibold">% salário</th>
            </tr>
          </thead>
          <tbody>
            {bankGroups.map((group, i) => (
              <tr
                key={group.banco}
                style={{ backgroundColor: i % 2 === 0 ? PDF_COLORS.white : PDF_COLORS.warmGray }}
              >
                <td
                  className="px-2 py-1.5 font-medium"
                  style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}` }}
                >
                  {group.banco}
                </td>
                <td
                  className="px-2 py-1.5 text-center"
                  style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}` }}
                >
                  {group.contratos}
                </td>
                <td
                  className="px-2 py-1.5 text-right font-semibold"
                  style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}`, color: PDF_COLORS.accentRed }}
                >
                  {formatCurrency(group.parcelaAtualCent)}
                </td>
                <td
                  className="px-2 py-1.5 text-right font-semibold"
                  style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}`, color: PDF_COLORS.accentGreen }}
                >
                  {formatCurrency(group.novaParcelaCent)}
                </td>
                <td
                  className="px-2 py-1.5 text-right"
                  style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}`, color: PDF_COLORS.accentGreen }}
                >
                  {formatCurrency(group.economiaCent)}
                </td>
                <td
                  className="px-2 py-1.5 text-right"
                  style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}` }}
                >
                  {formatPercent(group.percentSalario)}
                </td>
              </tr>
            ))}
            {/* Total row */}
            <tr style={{ backgroundColor: PDF_COLORS.lightGreen, fontWeight: 700 }}>
              <td
                className="px-2 py-1.5"
                style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}` }}
              >
                TOTAL
              </td>
              <td
                className="px-2 py-1.5 text-center"
                style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}` }}
              >
                {totalContratos}
              </td>
              <td
                className="px-2 py-1.5 text-right"
                style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}`, color: PDF_COLORS.accentRed }}
              >
                {formatCurrency(totalParcelaAtualCent)}
              </td>
              <td
                className="px-2 py-1.5 text-right"
                style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}`, color: PDF_COLORS.accentGreen }}
              >
                {formatCurrency(totalNovaParcelaCent)}
              </td>
              <td
                className="px-2 py-1.5 text-right"
                style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}`, color: PDF_COLORS.accentGreen }}
              >
                {formatCurrency(totalEconomiaCent)}
              </td>
              <td
                className="px-2 py-1.5 text-right"
                style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}` }}
              >
                -
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Commitment bars */}
      <div className="mt-4">
        <p className="mb-2 text-[11px] font-bold" style={{ color: PDF_COLORS.darkBlue }}>
          Comprometimento por banco
        </p>
        {bankGroups.map((group) => (
          <HorizontalCommitmentBar
            key={group.banco}
            label={group.banco}
            percent={group.percentSalario}
            valueCent={group.parcelaAtualCent}
          />
        ))}
      </div>

      {/* 3 summary boxes */}
      {hasProjectedTotals ? (
        <div className="mt-4 grid grid-cols-3 gap-3">
          <div
            className="rounded-sm px-3 py-2.5"
            style={{
              backgroundColor: PDF_COLORS.warmGray,
              border: `1px solid ${PDF_COLORS.borderGray}`,
            }}
          >
            <p
              className="text-[9px] font-semibold uppercase tracking-wide"
              style={{ color: PDF_COLORS.mediumGray }}
            >
              Total mantendo contratos
            </p>
            <p className="mt-1 text-[18px] font-bold" style={{ color: PDF_COLORS.accentRed }}>
              {formatCurrency(consolidatedSummary.totalAtualFinalCent)}
            </p>
          </div>
          <div
            className="rounded-sm px-3 py-2.5"
            style={{
              backgroundColor: PDF_COLORS.warmGray,
              border: `1px solid ${PDF_COLORS.borderGray}`,
            }}
          >
            <p
              className="text-[9px] font-semibold uppercase tracking-wide"
              style={{ color: PDF_COLORS.mediumGray }}
            >
              Total com nossos serviços
            </p>
            <p className="mt-1 text-[18px] font-bold" style={{ color: PDF_COLORS.accentGreen }}>
              {formatCurrency(consolidatedSummary.totalComReducaoFinalCent)}
            </p>
          </div>
          <div
            className="rounded-sm px-3 py-2.5"
            style={{
              backgroundColor: PDF_COLORS.warmGray,
              border: `1px solid ${PDF_COLORS.borderGray}`,
            }}
          >
            <p
              className="text-[9px] font-semibold uppercase tracking-wide"
              style={{ color: PDF_COLORS.mediumGray }}
            >
              Economia total projetada
            </p>
            <p className="mt-1 text-[18px] font-bold" style={{ color: PDF_COLORS.accentGreen }}>
              {formatCurrency(consolidatedSummary.economiaTotalFinalCent)}
            </p>
          </div>
        </div>
      ) : (
        <div
          className="mt-4 rounded-sm px-3 py-2.5 text-[9px]"
          style={{
            backgroundColor: PDF_COLORS.warmGray,
            border: `1px solid ${PDF_COLORS.borderGray}`,
            color: PDF_COLORS.textSecondary,
          }}
        >
          Totais finais não exibidos porque o documento não informa prazo de parcelas.
        </div>
      )}

      {consolidatedSummary.linhasSemPrazo > 0 && (
        <p className="mt-2 text-[8px]" style={{ color: PDF_COLORS.mediumGray }}>
          * {consolidatedSummary.linhasSemPrazo} linha(s) sem prazo identificado.
          Totais finais consideram apenas linhas com prazo.
        </p>
      )}
    </section>
  )
}
