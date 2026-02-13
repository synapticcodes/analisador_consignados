import { formatCurrency } from '@/types/api'
import { GrayBox, YellowCalloutBox } from './pdf-shared'
import { PDF_COLORS, type DetailedLoan } from './pdf-utils'

type DetailedBreakdownPageProps = {
  loans: DetailedLoan[]
}

export function DetailedBreakdownPage({ loans }: DetailedBreakdownPageProps) {
  const totalAtualCent = loans.reduce((s, l) => s + l.parcelaAtualCent, 0)
  const totalNovaCent = loans.reduce((s, l) => s + l.novaParcelaCent, 0)
  const totalReducaoCent = loans.reduce((s, l) => s + l.reducaoCent, 0)

  return (
    <section className="flex h-full flex-col" style={{ color: PDF_COLORS.textDark }}>
      <h2 className="text-[16px] font-bold" style={{ color: PDF_COLORS.darkBlue }}>
        Detalhamento por Empr&eacute;stimo
      </h2>
      <p className="mt-0.5 text-[10px]" style={{ color: PDF_COLORS.mediumGray }}>
        Vis&atilde;o individual de cada empr&eacute;stimo identificado no contracheque ou extrato.
      </p>

      {/* Yellow callout */}
      <div className="mt-2">
        <YellowCalloutBox title="Como ler esta tabela">
          <p>
            <strong>Parcela atual</strong> &eacute; o valor descontado hoje em folha.{' '}
            <strong>Nova parcela</strong> &eacute; o valor projetado ap&oacute;s a
            renegocia&ccedil;&atilde;o (redu&ccedil;&atilde;o de 75%).{' '}
            <strong>Redu&ccedil;&atilde;o</strong> &eacute; a diferen&ccedil;a mensal.{' '}
            <strong>Saldo restante</strong> &eacute; parcela atual &times; parcelas estimadas.
          </p>
        </YellowCalloutBox>
      </div>

      {/* Detailed table */}
      <div className="mt-3">
        <table className="w-full border-collapse text-[9px]">
          <thead>
            <tr style={{ backgroundColor: PDF_COLORS.darkBlue, color: PDF_COLORS.white }}>
              <th className="px-1.5 py-1.5 text-center font-semibold">#</th>
              <th className="px-1.5 py-1.5 text-left font-semibold">Banco / Tipo</th>
              <th className="px-1.5 py-1.5 text-right font-semibold">Parcela atual</th>
              <th className="px-1.5 py-1.5 text-right font-semibold">Nova parcela</th>
              <th className="px-1.5 py-1.5 text-right font-semibold">Redu&ccedil;&atilde;o</th>
              <th className="px-1.5 py-1.5 text-right font-semibold">Parcelas est.</th>
              <th className="px-1.5 py-1.5 text-right font-semibold">Saldo restante</th>
            </tr>
          </thead>
          <tbody>
            {loans.map((loan, i) => (
              <tr
                key={loan.index}
                style={{ backgroundColor: i % 2 === 0 ? PDF_COLORS.white : PDF_COLORS.warmGray }}
              >
                <td
                  className="px-1.5 py-1 text-center"
                  style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}` }}
                >
                  {loan.index}
                </td>
                <td
                  className="px-1.5 py-1"
                  style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}` }}
                >
                  <span className="font-medium">{loan.banco}</span>
                  <br />
                  <span style={{ color: PDF_COLORS.mediumGray }}>{loan.tipo}</span>
                </td>
                <td
                  className="px-1.5 py-1 text-right font-semibold"
                  style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}`, color: PDF_COLORS.accentRed }}
                >
                  {formatCurrency(loan.parcelaAtualCent)}
                </td>
                <td
                  className="px-1.5 py-1 text-right font-semibold"
                  style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}`, color: PDF_COLORS.accentGreen }}
                >
                  {formatCurrency(loan.novaParcelaCent)}
                </td>
                <td
                  className="px-1.5 py-1 text-right"
                  style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}`, color: PDF_COLORS.accentGreen }}
                >
                  {formatCurrency(loan.reducaoCent)}
                </td>
                <td
                  className="px-1.5 py-1 text-right"
                  style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}` }}
                >
                  {loan.parcelasEst ?? 'N/D'}
                </td>
                <td
                  className="px-1.5 py-1 text-right"
                  style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}` }}
                >
                  {loan.saldoRestanteCent !== null
                    ? formatCurrency(loan.saldoRestanteCent)
                    : 'N/D'}
                </td>
              </tr>
            ))}
            {/* Total row */}
            <tr style={{ backgroundColor: PDF_COLORS.lightGreen, fontWeight: 700 }}>
              <td
                className="px-1.5 py-1.5 text-center"
                style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}` }}
              >
                &mdash;
              </td>
              <td
                className="px-1.5 py-1.5"
                style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}` }}
              >
                TOTAL
              </td>
              <td
                className="px-1.5 py-1.5 text-right"
                style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}`, color: PDF_COLORS.accentRed }}
              >
                {formatCurrency(totalAtualCent)}
              </td>
              <td
                className="px-1.5 py-1.5 text-right"
                style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}`, color: PDF_COLORS.accentGreen }}
              >
                {formatCurrency(totalNovaCent)}
              </td>
              <td
                className="px-1.5 py-1.5 text-right"
                style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}`, color: PDF_COLORS.accentGreen }}
              >
                {formatCurrency(totalReducaoCent)}
              </td>
              <td
                className="px-1.5 py-1.5 text-right"
                style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}` }}
              >
                &mdash;
              </td>
              <td
                className="px-1.5 py-1.5 text-right"
                style={{ borderBottom: `1px solid ${PDF_COLORS.borderGray}` }}
              >
                &mdash;
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Gray transparency box */}
      <div className="mt-auto">
        <GrayBox title="Transparência sobre os cálculos">
          <p className="mb-1">
            A proje&ccedil;&atilde;o de &ldquo;nova parcela&rdquo; considera uma redu&ccedil;&atilde;o
            de 75% sobre o valor atual de cada parcela. Esse percentual reflete o hist&oacute;rico de
            resultados obtidos pela Credilly em a&ccedil;&otilde;es judiciais de revis&atilde;o de
            contratos consignados.
          </p>
          <p>
            Os resultados reais podem variar conforme o banco, o tipo de contrato e as
            condi&ccedil;&otilde;es espec&iacute;ficas de cada caso. Este documento n&atilde;o
            constitui garantia de resultado.
          </p>
        </GrayBox>
      </div>
    </section>
  )
}
