import { formatCurrency, type ConsignadoLineDetail } from '@/types/api'

type ConsignadoBreakdownProps = {
  lines: ConsignadoLineDetail[]
  title?: string
  showTotal?: boolean
  itemOffset?: number
  showConsolidatedSummary?: boolean
  summaryLines?: ConsignadoLineDetail[]
}

const REDUCED_PERCENT = 25

function compactLineLabel(line: ConsignadoLineDetail, maxLength = 96): string {
  const descricao =
    line.descricao_raw?.trim() ||
    line.descricao_canonica?.trim() ||
    line.descricao?.trim() ||
    'Sem descrição'
  const base = `${descricao} · Rub ${line.rubrica ?? '--'}`
  if (base.length <= maxLength) return base
  return `${base.slice(0, Math.max(0, maxLength - 1))}…`
}

function parsePrazo(line: ConsignadoLineDetail): number | null {
  if (typeof line.prazo === 'number' && Number.isFinite(line.prazo) && line.prazo > 0) {
    return Math.floor(line.prazo)
  }

  if (line.rubrica) {
    const trimmed = line.rubrica.trim()
    if (/^\d{2,3}$/.test(trimmed)) {
      const parsed = parseInt(trimmed, 10)
      if (parsed > 0 && parsed <= 120) return parsed
    }
  }

  return null
}

function computeReducedInstallment(parcelaCent: number): number {
  return Math.floor((parcelaCent * REDUCED_PERCENT) / 100)
}

type ConsolidatedSummary = {
  totalAtualFinalCent: number
  totalComReducaoFinalCent: number
  economiaTotalFinalCent: number
  totalParcelasMensaisAtuaisCent: number
  totalParcelasMensaisReducaoCent: number
  economiaMensalParcelasCent: number
  linhasSemPrazo: number
}

function buildConsolidatedSummary(lines: ConsignadoLineDetail[]): ConsolidatedSummary {
  let totalAtualFinalCent = 0
  let totalComReducaoFinalCent = 0
  let totalParcelasMensaisAtuaisCent = 0
  let totalParcelasMensaisReducaoCent = 0
  let linhasSemPrazo = 0

  for (const line of lines) {
    const parcelaAtualCent = line.valor_cent
    const parcelaReducaoCent = computeReducedInstallment(parcelaAtualCent)
    totalParcelasMensaisAtuaisCent += parcelaAtualCent
    totalParcelasMensaisReducaoCent += parcelaReducaoCent

    const prazo = parsePrazo(line)
    if (!prazo) {
      linhasSemPrazo += 1
      continue
    }

    totalAtualFinalCent += parcelaAtualCent * prazo
    totalComReducaoFinalCent += parcelaReducaoCent * prazo
  }

  return {
    totalAtualFinalCent,
    totalComReducaoFinalCent,
    economiaTotalFinalCent: totalAtualFinalCent - totalComReducaoFinalCent,
    totalParcelasMensaisAtuaisCent,
    totalParcelasMensaisReducaoCent,
    economiaMensalParcelasCent:
      totalParcelasMensaisAtuaisCent - totalParcelasMensaisReducaoCent,
    linhasSemPrazo,
  }
}

export function ConsignadoBreakdown({
  lines,
  title = 'Linhas do Contracheque',
  showTotal = true,
  itemOffset = 0,
  showConsolidatedSummary = false,
  summaryLines,
}: ConsignadoBreakdownProps) {
  if (lines.length === 0) return null

  const total = lines.reduce((acc, item) => acc + item.valor_cent, 0)
  const consolidatedSummary = buildConsolidatedSummary(summaryLines ?? lines)

  return (
    <section className="space-y-2">
      <h3 className="text-xl font-semibold text-slate-900">{title}</h3>
      <p className="text-xs text-slate-600">
        Simulação por linha considerando redução de 75% na parcela mensal.
      </p>

      <div className="space-y-2">
        {lines.map((line, index) => {
          const parcelaAtualCent = line.valor_cent
          const prazo = parsePrazo(line)
          const novaParcelaCent = computeReducedInstallment(parcelaAtualCent)
          const valorTotalAtualCent = prazo ? parcelaAtualCent * prazo : null
          const valorTotalReduzidoCent = prazo ? novaParcelaCent * prazo : null
          const valorEconomiaTotalCent =
            valorTotalAtualCent !== null && valorTotalReduzidoCent !== null
              ? valorTotalAtualCent - valorTotalReduzidoCent
              : null
          const displayIndex = itemOffset + index + 1

          return (
            <div
              key={`${line.descricao_raw ?? line.descricao_canonica ?? line.descricao}-${index}`}
              className="rounded-lg border border-slate-200 bg-slate-50 p-2"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-slate-900">Empréstimo {displayIndex}</p>
                <p className="rounded-md bg-red-50 px-2 py-0.5 text-sm font-bold text-red-700">
                  {formatCurrency(parcelaAtualCent)}
                </p>
              </div>
              <p className="mt-1 truncate text-xs leading-tight text-slate-600">
                {compactLineLabel(line)}
              </p>

              <div className="mt-1 grid grid-cols-2 gap-x-2 gap-y-1 text-[11px] leading-tight text-slate-700">
                <div className="rounded-md border border-red-200 bg-red-50 px-2 py-1">
                  <p className="font-semibold text-slate-900">Parcela atual:</p>
                  <p className="font-bold text-red-700">{formatCurrency(parcelaAtualCent)}</p>
                </div>
                <div className="rounded-md border border-slate-200 bg-white px-2 py-1">
                  <p className="font-semibold text-slate-900">Quantidade estimada de parcelas:</p>
                  <p className="font-semibold text-slate-800">{prazo ?? 'não consta'}</p>
                </div>
                <div className="rounded-md border border-red-200 bg-red-50 px-2 py-1">
                  <p className="font-semibold text-slate-900">Valor total mantendo o contrato atual:</p>
                  <p className="font-bold text-red-700">
                    {valorTotalAtualCent !== null ? formatCurrency(valorTotalAtualCent) : 'não consta'}
                  </p>
                </div>
                <div className="rounded-md border border-emerald-200 bg-emerald-50 px-2 py-1">
                  <p className="font-semibold text-slate-900">Nova parcela com nossos serviços:</p>
                  <p className="font-bold text-emerald-700">{formatCurrency(novaParcelaCent)}</p>
                </div>
                <div className="rounded-md border border-emerald-200 bg-emerald-50 px-2 py-1">
                  <p className="font-semibold text-slate-900">Valor total com a redução:</p>
                  <p className="font-bold text-emerald-700">
                    {valorTotalReduzidoCent !== null ? formatCurrency(valorTotalReduzidoCent) : 'não consta'}
                  </p>
                </div>
                <div className="rounded-md border border-emerald-300 bg-emerald-100 px-2 py-1">
                  <p className="font-semibold text-slate-900">Valor total reduzido neste empréstimo:</p>
                  <p className="font-extrabold text-emerald-800">
                    {valorEconomiaTotalCent !== null ? formatCurrency(valorEconomiaTotalCent) : 'não consta'}
                  </p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {showTotal && (
        <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-900">
          <p>Total consignados</p>
          <p>{formatCurrency(total)}</p>
        </div>
      )}

      {showConsolidatedSummary && (
        <div className="rounded-lg border border-slate-200 bg-white p-3">
          <h4 className="text-sm font-semibold text-slate-900">Resumo geral consolidado</h4>
          <div className="mt-2 space-y-1 text-xs text-slate-700">
            <p>
              Valor total que o cliente pagaria ao final de todos os empréstimos mantendo os
              contratos atuais:{' '}
              <span className="font-semibold text-red-700">
                {formatCurrency(consolidatedSummary.totalAtualFinalCent)}
              </span>
            </p>
            <p>
              Valor total com nossos serviços:{' '}
              <span className="font-semibold text-emerald-700">
                {formatCurrency(consolidatedSummary.totalComReducaoFinalCent)}
              </span>
            </p>
            <p>
              Valor total de economia:{' '}
              <span className="font-bold text-emerald-800">
                {formatCurrency(consolidatedSummary.economiaTotalFinalCent)}
              </span>
            </p>
            <p>
              Valor total das parcelas mensais atuais:{' '}
              <span className="font-semibold text-red-700">
                {formatCurrency(consolidatedSummary.totalParcelasMensaisAtuaisCent)}
              </span>
            </p>
            <p>
              Valor total das parcelas mensais com nossos serviços:{' '}
              <span className="font-semibold text-emerald-700">
                {formatCurrency(consolidatedSummary.totalParcelasMensaisReducaoCent)}
              </span>
            </p>
            <p>
              Redução mensal no valor das parcelas:{' '}
              <span className="font-bold text-emerald-800">
                {formatCurrency(consolidatedSummary.economiaMensalParcelasCent)}
              </span>
            </p>
          </div>
          {consolidatedSummary.linhasSemPrazo > 0 && (
            <p className="mt-2 text-[11px] text-slate-500">
              Linhas sem prazo identificado: {consolidatedSummary.linhasSemPrazo}. Totais finais
              de contrato consideram apenas linhas com prazo.
            </p>
          )}
        </div>
      )}
    </section>
  )
}
