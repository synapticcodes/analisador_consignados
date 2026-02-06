import { formatCurrency, type FinalResultResponse } from '@/types/api'

type CoverSummaryProps = {
  result: FinalResultResponse
  clientName?: string
  dateLabel: string
}

function metricLabel(label: string, value: number | null) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-semibold text-slate-900">{formatCurrency(value)}</p>
    </div>
  )
}

export function CoverSummary({ result, clientName, dateLabel }: CoverSummaryProps) {
  const economiaMensal =
    result.divida_mensal_cent !== null && result.divida_mensal_reduzida_cent !== null
      ? result.divida_mensal_cent - result.divida_mensal_reduzida_cent
      : null

  return (
    <section className="flex h-full flex-col">
      <header className="border-b border-slate-200 pb-4">
        <p className="text-xs uppercase tracking-wide text-slate-500">Diagnóstico Financeiro</p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">Retrato Financeiro</h1>
        <p className="mt-1 text-sm text-slate-600">
          {clientName ? `Cliente: ${clientName} • ` : ''}Data: {dateLabel}
        </p>
      </header>

      <div className="mt-6 grid grid-cols-2 gap-4">
        {metricLabel('Salário Bruto', result.salario_bruto_cent)}
        {metricLabel('Salário Líquido', result.salario_liquido_cent)}
        {metricLabel('Total de Descontos', result.total_descontos_cent)}
        {metricLabel('Dívida Mensal (90%)', result.divida_mensal_cent)}
      </div>

      <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
        <p className="text-sm uppercase tracking-wide text-emerald-700">Economia estimada</p>
        <p className="mt-2 text-4xl font-semibold text-emerald-900">
          {formatCurrency(economiaMensal)}
        </p>
        <p className="mt-2 text-sm text-emerald-900">
          Cenário atual: {formatCurrency(result.divida_mensal_cent)} / mês
        </p>
        <p className="text-sm text-emerald-900">
          Cenário reduzido: {formatCurrency(result.divida_mensal_reduzida_cent)} / mês
        </p>
      </div>
    </section>
  )
}
